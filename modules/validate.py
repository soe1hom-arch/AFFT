# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0
# By. soe1hom-arch / Wandi
# ============================================================
# Tool ini dilindungi hak cipta. Dilarang menghapus atau
# mengubah kredit penulis tanpa izin.
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
