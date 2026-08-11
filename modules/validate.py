# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.2
# Author. soe1hom-arch / Wandi
# ============================================================

import struct
from pathlib import Path

from .common import resolve_binary


def required_binaries_present() -> bool:
    """Cek apakah binary wajib sudah tersedia.
    
    Jika lucky-arch tersedia, lpunpack dan simg2img tidak diperlukan
    untuk unpack super.img (lucky-arch menggabungkan keduanya).
    """
    required = [
        "payload-dumper-go",
        "extract.erofs",
        "debugfs",
        "magiskboot",
    ]
    # lucky-arch bisa menggantikan lpunpack + simg2img untuk unpack super.img
    if not resolve_binary("lucky-arch"):
        required.extend(["lpunpack", "simg2img"])
    
    missing = [name for name in required if resolve_binary(name) is None]
    if missing:
        print(f"[!] Missing required binaries: {', '.join(missing)}")
        return False
    return True


def is_sparse_image(path: Path) -> bool:
    """Cek apakah file adalah Android sparse image (magic: 0xED26FF3A)."""
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
        return len(magic) == 4 and struct.unpack("<I", magic)[0] == 0xED26FF3A
    except Exception:
        return False


def detect_fs_type(path: Path) -> str:
    """Deteksi tipe filesystem dari magic bytes.
    
    Supports:
      - EROFS  (magic at offset 0: 0x00F5E1E2)
      - ext4   (magic at offset 0x438: 0xEF53)
      - F2FS   (magic at offset 0: 0xF2F52010)
      - gzip   (magic at offset 0: 0x1F8B)
    
    Returns:
        "erofs", "ext4", "f2fs", "gzip", or "unknown"
    """
    if not path.exists():
        return "unknown"
    
    # Skip sparse images
    if is_sparse_image(path):
        return "unknown"
    
    try:
        with open(path, "rb") as f:
            # Baca 4 byte pertama
            magic4 = f.read(4)
            # ext4 superblock ada di offset 0x400, magic di offset 0x438
            f.seek(0x438)
            ext4_magic = f.read(2)
    except Exception:
        return "unknown"

    # EROFS: 0x00F5E1E2 (little-endian)
    if len(magic4) == 4 and magic4 == b'\xe2\xe1\xf5\x00':
        return "erofs"

    # F2FS: 0xF2F52010 atau 0x1020F5F2
    if len(magic4) == 4 and magic4 in (b'\x10\x20\xf5\xf2', b'\xf2\xf5\x20\x10'):
        return "f2fs"

    # gzip: 0x1F8B
    if len(magic4) >= 2 and magic4[:2] == b'\x1f\x8b':
        return "gzip"

    # ext4: 0xEF53 at offset 0x438
    if len(ext4_magic) == 2 and ext4_magic == b'\x53\xef':
        return "ext4"

    return "unknown"


def raw_to_sparse(raw_path: Path, sparse_path: Path, block_size: int = 4096) -> bool:
    """Konversi raw image ke Android sparse format (multi-chunk support untuk >4GB)."""
    try:
        raw_data = raw_path.read_bytes()
        data_len = len(raw_data)
        
        blocks = (data_len + block_size - 1) // block_size
        padded_len = blocks * block_size
        
        max_uint32 = 4294967295
        chunk_hdr_sz = 12
        file_hdr_sz = 28
        
        # Max blocks per chunk agar total_sz (chunk_hdr_sz + data) tidak overflow uint32
        max_blocks_per_chunk = (max_uint32 - chunk_hdr_sz) // block_size
        
        if max_blocks_per_chunk <= 0:
            print(f"  [ERROR] Block size terlalu besar")
            return False
        
        # Jika muat 1 chunk, tulis langsung
        if blocks <= max_blocks_per_chunk and (chunk_hdr_sz + padded_len) <= max_uint32:
            sparse_header = struct.pack(
                "<IHHHHIIII",
                0xED26FF3A,
                1, 0,
                file_hdr_sz, chunk_hdr_sz,
                block_size,
                blocks,
                1,  # 1 chunk
                0,
            )
            chunk_header = struct.pack(
                "<HHII",
                0xCAC1,  # RAW
                0,
                blocks,
                chunk_hdr_sz + padded_len,
            )
            with open(sparse_path, "wb") as f:
                f.write(sparse_header)
                f.write(chunk_header)
                f.write(raw_data)
                if padded_len > data_len:
                    f.write(b'\x00' * (padded_len - data_len))
            return True
        
        # Image besar: split menjadi multiple RAW chunks
        size_gb = data_len / (1024**3)
        num_chunks = (blocks + max_blocks_per_chunk - 1) // max_blocks_per_chunk
        print(f"  [INFO] Image besar ({size_gb:.1f}GB), split jadi {num_chunks} RAW chunks")
        
        sparse_header = struct.pack(
            "<IHHHHIIII",
            0xED26FF3A,
            1, 0,
            file_hdr_sz, chunk_hdr_sz,
            block_size,
            blocks,
            num_chunks,
            0,
        )
        
        with open(sparse_path, "wb") as f:
            f.write(sparse_header)
            
            offset = 0
            remaining = blocks
            while remaining > 0:
                chunk_blocks = min(remaining, max_blocks_per_chunk)
                chunk_data_len = chunk_blocks * block_size
                chunk_total_sz = chunk_hdr_sz + chunk_data_len
                
                chunk_header = struct.pack(
                    "<HHII",
                    0xCAC1,  # RAW
                    0,
                    chunk_blocks,
                    chunk_total_sz,
                )
                f.write(chunk_header)
                data_start = offset
                data_end = min(offset + chunk_data_len, data_len)
                f.write(raw_data[data_start:data_end])
                # Padding untuk block boundary
                pad = chunk_data_len - (data_end - data_start)
                if pad > 0:
                    f.write(b'\x00' * pad)
                
                offset += chunk_data_len
                remaining -= chunk_blocks
        
        print(f"  [INFO] Sparse multi-chunk selesai: {num_chunks} chunks")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Konversi raw->sparse gagal: {e}")
        return False
