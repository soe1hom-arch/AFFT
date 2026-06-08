# Android Firmware Full Toolkit (AFFT)

**Versi 2.0**  
*By. soe1hom-arch / Wandi*

Android Firmware Full Toolkit (AFFT) adalah alat lengkap untuk memodifikasi firmware Android. Mendukung bongkar-pasang `payload.bin`, `super.img`, filesystem (EROFS/ext4), dan boot image.

## Fitur

- **Extract payload.bin** — Bongkar OTA firmware Android
- **Unpack/Repack super.img** — Bongkar & rakit logical partitions
- **Extract/Repack filesystem** — EROFS & ext4
- **Boot family** — Unpack/repack boot.img, vendor_boot.img, init_boot.img
- **Sparse image** — Deteksi & konversi otomatis (simg2img)
- **Binary resolver** — Cari binary otomatis (PATH → $HOME/ → bin/)

## Struktur Folder

```
AFFT/
├── main.py              ← Program utama
├── modules/             ← Modul Python
│   ├── __init__.py
│   ├── boot.py          ← Boot image handler
│   ├── common.py        ← Fungsi bantuan umum
│   ├── filesystem.py    ← Extract & repack filesystem
│   ├── super.py         ← Unpack & repack super.img
│   └── validate.py      ← Validasi image
├── bin/                 ← Binary tools (9 binary)
│   ├── payload-dumper-go
│   ├── lpunpack / lpmake
│   ├── simg2img
│   ├── extract.erofs / mkfs.erofs
│   ├── debugfs / make_ext4fs
│   └── magiskboot
├── input/               ← Tempatkan file firmware di sini
├── output/              ← Hasil extract/repack
├── temp/                ← File sementara (dibersihkan otomatis)
└── logs/                ← Catatan log
```

## Cara Pakai

```bash
cd AFFT
python main.py
```

### Menu Utama

```
[1] Extract payload.bin
[2] Unpack / Repack super.img
[3] Extract / Repack filesystem IMG
[4] Boot family (unpack/repack)
[5] Clean output
[6] Exit
```

## Persyaratan Sistem

- **Termux** di Android (recommended) atau **Linux aarch64**
- **Python 3.8+**
- **Storage HP** minimal 20-30 GB untuk firmware besar

## Install di Termux

### Otomatis (via install-termux.sh):
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/soe1hom-arch/android-firmware-toolkit/main/install-termux.sh)
```

### Manual:
```bash
pkg update && pkg upgrade
pkg install python git wget
git clone https://github.com/soe1hom-arch/android-firmware-toolkit
cd android-firmware-toolkit
python main.py
```

## Binary Tools

| Binary | Wajib? | Fungsi |
|--------|--------|--------|
| `payload-dumper-go` | ✅ Wajib | Extract payload.bin |
| `lpunpack` | ✅ Wajib | Unpack super.img |
| `simg2img` | ✅ Wajib | Konversi sparse ke raw |
| `extract.erofs` | ✅ Wajib | Extract EROFS |
| `debugfs` | ✅ Wajib | Extract ext4 |
| `magiskboot` | ✅ Wajib | Unpack/repack boot |
| `lpmake` | ⬜ Opsional | Repack super.img |
| `mkfs.erofs` | ⬜ Opsional | Repack EROFS |
| `make_ext4fs` | ⬜ Opsional | Repack ext4 |

## Kredit

- **Developer**: soe1hom-arch / Wandi
- **payload-dumper-go**: ssut
- **lpunpack / lpmake / simg2img**: AOSP
- **extract.erofs / mkfs.erofs**: erofs-utils (NDK by sekaiacg)
- **debugfs**: e2fsprogs (Tsurugi Linux)
- **make_ext4fs**: rendiix
- **magiskboot**: topjohnwu (Magisk)

## Lisensi

MIT License — lihat `LICENSE` untuk detail.
