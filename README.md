# Android Firmware Full Toolkit (AFFT)

**Versi 2.0.2**  
*Author. soe1hom-arch / Wandi*

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


## Fitur Baru v2.0.2

### Debug Mode [D]

Tekan `D` di menu utama untuk mengaktifkan/mematikan mode debug.

```
Select Menu : D
[V] Debug mode: ON
```

Saat ON, semua operasi menampilkan info detail:
- **Unpack filesystem**: deteksi tipe (erofs/ext4), skip firmware
- **Repack filesystem**: perintah mkfs yang dijalankan, ref_img yang dipakai
- **Super unpack**: parameter lpunpack
- **Payload extract**: file .img yang ditemukan
- **Repack loop**: direktori diproses, status src_img

---

### Wizard Mode [W]

Tekan `W` di menu utama untuk mode wizard. Tools akan auto-scan folder dan kasih pilihan tindakan:

```
  [W] Wizard mode - auto scan & choose action
```

Alurnya:

```
Scanning for .img files and contents...
  [i] Found 45 .img files
  [i] Found 18 content directories

  [1] Unpack .img files to filesystem contents
  [2] Repack content directories to .img files
  [3] Choose custom folder
  [4] Back
```

**Opsi 1 — Unpack .img files:**
Pilih sumber .img (dari `input/`, `temp/img/`, `temp/payload/` atau semua), lalu extract filesystem-nya ke `temp/contents/`.

```
Choose source:
  [1] input/ (10 files)
  [2] temp/img/ (45 files)
  [3] All sources
```

**Opsi 2 — Repack content directories:**
Pilih direktori mana yang mau direpack (satu per satu, semua, atau folder kustom).

```
Content directories available:
  [1] mi_ext      [5] product      [9] system_dlkm    [13] vendor
  [2] mi_ext_a   [6] product_a    [10] system_dlkm_a  [14] vendor_a
  [3] odm        [7] system       [11] system_ext     [15] vendor_dlkm
  [4] odm_a      [8] system_a     [12] system_ext_a   [16] vendor_dlkm_a
  [A] All
  [C] Choose custom folder
```

**Opsi 3 — Choose custom folder:**
Masukkan path folder manual, lalu pilih unpack atau repack.

```
Enter folder path: /sdcard/Download/my_images

  [1] Unpack .img files in this folder
  [2] Repack subdirectories to .img
  [3] Back
```

---

### Firmware Skip (42 partisi otomatis dilewati)

Partisi firmware/bootloader berikut otomatis di-skip saat extract/repack filesystem, karena bukan filesystem yang bisa diekstrak:

`abl`, `aop`, `aop_config`, `bluetooth`, `boot`, `countrycode`, `cpucp`, `cpucp_dtb`, `devcfg`, `dsp`, `dtbo`, `featenabler`, `hyp`, `idmanager`, `imagefv`, `init_boot`, `keymaster`, `modem`, `modemfirmware`, `multiimgqti`, `pvmfw`, `qupfw`, `recovery`, `shrm`, `slim_audiop`, `soccp_dcd`, `soccp_debug`, `spuservice`, `storage`, `tz`, `uefi`, `uefisecapp`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor`, `vendor_boot`, `vendor_kernel_boot`, `vm-bootsys`, `xbl`, `xbl_config`, `xbl_ramdump`, `xm_edid`

---

### Multi-Chunk Sparse (>4GB)

`raw_to_sparse` sekarang support image >4GB (seperti `product.img` hingga 5GB+).
Data otomatis dipecah menjadi beberapa RAW chunk agar muat dalam format Android sparse.

```
[INFO] Image besar (4.8GB), split jadi 2 RAW chunks
[INFO] Sparse multi-chunk selesai: 2 chunks
```

---

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

## Catatan Rilis v2.0 → v2.0.2

**v2.0.2** — Perbaikan bug & fitur baru:
- ✅ **Fix raw_to_sparse** — struct.pack format & multi-chunk untuk image >4GB
- ✅ **Fix stray continue** — repack loop tidak lagi skip semua direktori
- ✅ **Fix firmware crash** — 42 partisi non-filesystem otomatis di-skip
- ✅ **Wizard mode [W]** — auto-scan, pilih sumber, unpack/repack kustom
- ✅ **Debug mode [D]** — toggle global untuk semua module
- ✅ **Output konsisten** — cleanup folder sebelum ekstrak ulang
- ✅ **Error handling** — cleanup partial extraction on failure

**v2.0.1** — Perbaikan & penambahan fitur:
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
