# Android Firmware Full Toolkit (AFFT)

**Versi 2.0.1**  
*By. soe1hom-arch / Wandi*

Android Firmware Full Toolkit (AFFT) adalah alat lengkap untuk memodifikasi firmware Android. Mendukung bongkar-pasang `payload.bin`, `super.img`, filesystem (EROFS/ext4), dan boot image.

## Fitur

- **Extract payload.bin** — Bongkar OTA firmware Android
- **Unpack/Repack super.img** — Bongkar & rakit logical partitions
- **Extract/Repack filesystem** — EROFS & ext4 (otomatis sparse)
- **Boot family** — Unpack/repack boot, recovery, dtbo, vendor_boot, init_boot, vbmeta, vendor_kernel_boot
- **Sparse image** — Deteksi, konversi raw↔sparse otomatis (termasuk hasil repack)
- **Batch mode** — Extract/repack satu-satu atau semua sekaligus
- **Unified storage** — Semua hasil operasi tersimpan di `temp/` dan saling terhubung

## Struktur Folder

```
AFFT/
├── main.py              ← Program utama
├── modules/             ← Modul Python
│   ├── __init__.py
│   ├── boot.py          ← Boot image handler (6 tipe boot)
│   ├── common.py        ← Fungsi bantuan umum (path, binary resolver)
│   ├── filesystem.py    ← Extract & repack filesystem (+ sparse konversi)
│   ├── super.py         ← Unpack & repack super.img
│   └── validate.py      ← Validasi image (sparse, deteksi FS, raw2sparse)
├── bin/                 ← Binary tools (9 binary)
├── input/               ← 🔵 Tempatkan FIRMWARE ASLI di sini
├── temp/                ← 🟢 Semua hasil kerja ada di sini
│   ├── img/             ← File .img partisi (dari payload, super unpack, repack fs)
│   ├── contents/        ← Folder filesystem hasil extract
│   ├── repacked/        ← Hasil repack super.img (super_repack.img)
│   ├── payload/         ← Hasil extract payload.bin
│   ├── boot_out/        ← Hasil unpack/repack boot image (*_repack.img)
│   └── logs/            ← Catatan log
```

## Alur Kerja Terpadu

```
input/super.img ──→ [2] Unpack ──→ temp/img/*.img ──→ [3] Extract FS ──→ temp/contents/
                                                                │
input/payload.bin ──→ [1] Extract ──→ temp/img/*.img ──→ [3] Extract FS ──→ temp/contents/
                                                                │
temp/contents/ ──→ [3] Repack ──→ temp/img/*_repack.img ──→ [2] Repack super ──→ temp/repacked/super_repack.img
```

**Semua hasil dari menu mana saja bisa langsung dipakai menu lain**, tanpa perlu copy file manual.

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
[4] Boot family (unpack/repack) — 6 tipe boot
[5] Clean output
[6] Exit
```

### Menu 4: Boot Family (v2.0.1 — 6 tipe boot)

```
[1] Check boot family
[2] Unpack boot/recovery/dtbo
[3] Unpack vendor_boot/init_boot
[4] Unpack vbmeta/vendor_kernel_boot
[5] Repack boot/recovery/dtbo
[6] Repack vendor_boot/init_boot
[7] Repack vbmeta/vendor_kernel_boot
[8] Back
```

### Hasil Repack — Penamaan Spesifik

Semua hasil repack diberi akhiran `_repack.img` agar mudah dikenali:
- `super_repack.img`
- `boot_repack.img`, `vendor_boot_repack.img`, `init_boot_repack.img`
- `system_repack.img`, `vendor_repack.img`, `product_repack.img`, dll.

## Persyaratan Sistem

- **Termux** di Android (recommended) atau **Linux aarch64**
- **Python 3.8+**
- **Storage HP** minimal 20-30 GB untuk firmware besar

## Install di Termux

### Otomatis (via install-termux.sh):
```bash
bash <(wget -qO- https://raw.githubusercontent.com/soe1hom-arch/AFFT/main/install-termux.sh)
```

### Manual:
```bash
pkg update && pkg upgrade
pkg install python git wget
git clone https://github.com/soe1hom-arch/AFFT
cd AFFT
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
| `magiskboot` | ✅ Wajib | Unpack/repack boot (6 tipe) |
| `lpmake` | ⬜ Opsional | Repack super.img (sparse) |
| `mkfs.erofs` | ⬜ Opsional | Repack EROFS (+ sparse) |
| `make_ext4fs` | ⬜ Opsional | Repack ext4 (built-in sparse) |

## Catatan Rilis v2.0 → v2.0.1

**v2.0.1** menghadirkan perbaikan penting dan penambahan fitur:
- ✅ **Fix vendor_boot.img unpack** — exit code 3 bukan error (vendor_boot detected)
- ✅ **Fix repack boot** — file sumber tidak dihapus setelah unpack
- ✅ **6 tipe boot** — boot, recovery, dtbo, vendor_boot, init_boot, vbmeta, vendor_kernel_boot
- ✅ **Repack sparse** — hasil repack filesystem otomatis di-sparse-kan
- ✅ **Penamaan repack jelas** — `*_repack.img` untuk semua hasil repack
- ✅ **Menu boot dirombak** — 3 kategori dengan sub-menu repack spesifik

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
