# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.1
# Author. soe1hom-arch / Wandi
# ============================================================

import struct
from pathlib import Path

from .common import resolve_binary


def required_binaries_present() -> bool:
    """Cek apakah binary wajib sudah tersedia."""
    required = [
        "payload-dumper-go",
        "lpunpack",
        "simg2img",
        "extract.erofs",
        "debugfs",
        "magiskboot",
    ]
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
    """Konversi raw image ke Android sparse format.
    
    Args:
        raw_path: Path ke raw image
        sparse_path: Path output untuk sparse image
        block_size: Block size (default 4096)
    
    Returns:
        True jika berhasil, False jika gagal
    """
    try:
        raw_data = raw_path.read_bytes()
        data_len = len(raw_data)
        
        # Hitung block
        blocks = (data_len + block_size - 1) // block_size
        padded_len = blocks * block_size
        
        # Sparse header: 28 bytes
        # struct: magic(4) major(2) minor(2) file_hdr_sz(2) chunk_hdr_sz(2)
        #         blk_sz(4) total_blks(4) total_chunks(4) crc32(4)
        file_hdr_sz = 28
        chunk_hdr_sz = 12
        total_sz = file_hdr_sz + chunk_hdr_sz + padded_len
        
        sparse_header = struct.pack(
            "<IHHIIIII",
            0xED26FF3A,  # magic
            1,            # major_version
            0,            # minor_version
            file_hdr_sz,  # file_hdr_sz
            chunk_hdr_sz, # chunk_hdr_sz
            block_size,   # blk_sz
            blocks,       # total_blks
            1,            # total_chunks (1 RAW chunk)
            0,            # crc32 (optional)
        )
        
        # Chunk header: 12 bytes
        # struct: chunk_type(2) reserved(2) chunk_sz(4) total_sz(4)
        chunk_header = struct.pack(
            "<HHII",
            0xCAC1,  # chunk_type: RAW
            0,       # reserved
            blocks,  # chunk_sz in blocks
            chunk_hdr_sz + padded_len,  # total_sz: header + data
        )
        
        # Write sparse file
        with open(sparse_path, "wb") as f:
            f.write(sparse_header)
            f.write(chunk_header)
            f.write(raw_data)
            # Padding ke block_size
            if padded_len > data_len:
                f.write(b'\x00' * (padded_len - data_len))
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Konversi raw->sparse gagal: {e}")
        return False
