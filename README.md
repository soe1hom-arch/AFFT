# Android Firmware Full Toolkit (AFFT)

**Versi 2.0**  
*By. soe1hom-arch / Wandi*

Android Firmware Full Toolkit (AFFT) adalah alat untuk memodifikasi firmware Android. Mendukung bongkar-pasang `payload.bin`, `super.img`, filesystem (EROFS/ext4), dan boot image.

## Fitur

- **Extract payload.bin** — Bongkar OTA firmware
- **Unpack/Repack super.img** — Bongkar & rakit logical partitions
- **Extract/Repack filesystem** — EROFS & ext4
- **Boot family** — Unpack/repack boot.img, vendor_boot.img, init_boot.img
- **Sparse image** — Deteksi & konversi otomatis
- **Binary resolver** — Cari binary otomatis (PATH → $HOME/ → bin/)

## Struktur Folder

```
AFFT/
├── main.py              ← Program utama
├── modules/             ← Modul Python
│   ├── boot.py          ← Boot image handler
│   ├── common.py        ← Fungsi bantuan umum
│   ├── filesystem.py    ← Extract & repack filesystem
│   ├── super.py         ← Unpack & repack super.img
│   └── validate.py      ← Validasi image
├── bin/                 ← Binary tools
├── input/               ← Tempat file firmware
├── output/              ← Hasil extract/repack
├── temp/                ← File sementara
└── logs/                ← Catatan log
```

## Cara Pakai

```bash
cd AFFT
python main.py
```

## Persyaratan

- Termux (Android) atau Linux aarch64
- Python 3.8+
- Storage cukup (20-30 GB untuk firmware besar)

## Kredit

Binary tools dari berbagai sumber:
- `payload-dumper-go` — ssut
- `lpunpack` / `lpmake` / `simg2img` — AOSP
- `extract.erofs` / `mkfs.erofs` — erofs-utils (NDK by sekaiacg)
- `debugfs` — e2fsprogs (Tsurugi Linux)
- `make_ext4fs` — rendiix
- `magiskboot` — topjohnwu (Magisk)
