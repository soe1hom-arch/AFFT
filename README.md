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
- **lucky-arch** — Unpack super.img satu langkah, tanpa intermediate raw file di disk
- **Batch mode** — Extract/repack satu-satu atau semua sekaligus
- **Wizard mode [W]** — Auto-scan folder untuk .img & content directories
- **Debug mode [D]** — Toggle global untuk info detail proses
- **Unified storage** — Semua hasil operasi tersimpan di `temp/` dan saling terhubung

## Struktur Folder

```
AFFT/
├── main.py              ← Program utama
├── modules/             ← Modul Python
│   ├── __init__.py
│   ├── boot.py          ← Boot image handler (7 tipe boot)
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
│   ├── img_src/         ← Working directory super unpack
│   ├── filesystem_work/ ← Working directory repack filesystem
│   ├── boot/            ← Working directory boot unpack
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

---

## Cara Pakai

```bash
cd AFFT
python main.py
```

### Menu Utama

```
╔══════════════════════════════════════════════╗
║      ANDROID FIRMWARE FULL TOOLKIT           ║
║      AFFT v2.0.2                             ║
║      Author. soe1hom-arch / Wandi            ║
╚══════════════════════════════════════════════╝

[1] Extract payload.bin
[2] Unpack super.img
[3] Extract filesystem IMG
[4] Boot family (unpack/repack)
[5] Clean output
[W] Wizard mode - auto scan & choose action
[D] Toggle debug mode (current: OFF)
[6] Exit

Select Menu :
```

---

### [1] Extract payload.bin

```
╔══════════════════════════════════════════════╗
║            EXTRACT PAYLOAD.BIN             ║
╚══════════════════════════════════════════════╝

[1] Extract payload.bin to temp/payload/
[2] Extract payload.bin to temp/img/
[3] Back
```

- **Opsi 1**: Extract payload.bin → semua partisi .img disimpan ke `temp/payload/`
- **Opsi 2**: Extract payload.bin → semua partisi .img disimpan ke `temp/img/` (untuk diproses lebih lanjut)

File `payload.bin` harus ditempatkan di folder **`input/`** sebelum menjalankan menu ini.

---

### [2] Unpack super.img

```
╔══════════════════════════════════════════════╗
║                SUPER.IMG                   ║
╚══════════════════════════════════════════════╝

[1] Unpack super.img (partisi saja)
[2] Unpack super.img + extract filesystem
[3] Repack super.img
[4] Back
```

- **Opsi 1**: Unpack `super.img` → semua partisi .img diekstrak ke `temp/img/`
- **Opsi 2**: Unpack `super.img` + otomatis extract filesystem dari setiap partisi ke `temp/contents/` (menyatu dengan menu 3)
- **Opsi 3**: Repack `super_repack.img` dari partisi-partisi yang ada di `temp/img/` menggunakan `lpmake` (sparse output)

File `super.img` harus ditempatkan di folder **`input/`**.

---

### [3] Extract / Repack Filesystem IMG

```
╔══════════════════════════════════════════════╗
║         FILESYSTEM (EROFS/ext4)            ║
╚══════════════════════════════════════════════╝

[1] Unpack filesystem IMG (pilih satu)
[2] Unpack all filesystem IMG
[3] Repack filesystem (pilih satu)
[4] Repack all contents
[5] Back
```

#### Opsi 1 — Unpack satu partisi

Pilih file .img dari daftar yang ditemukan di `temp/img/`:

```
Pilih file IMG
[1] system.img (4.2 GB)
[2] vendor.img (1.1 GB)
[3] product.img (4.8 GB)
...
[0] Back
```

#### Opsi 2 — Unpack semua partisi

Ekstrak semua .img yang valid (otomatis skip 42 partisi firmware!).

#### Opsi 3 — Repack satu direktori

Pilih folder dari `temp/contents/` untuk direpack menjadi .img:

```
Pilih direktori
[1] system (4.2 GB)
[2] vendor (1.1 GB)
[3] product (4.8 GB)
...
[0] Back
```

#### Opsi 4 — Repack semua contents

Repack semua direktori di `temp/contents/` jadi .img di `temp/img/` (otomatis sparse).

**Filesystem yang didukung:**
- **EROFS** — Menggunakan `mkfs.erofs` (lz4 default)
- **ext4** — Menggunakan `make_ext4fs` (sparse otomatis dengan `-s`) atau `mkfs.ext4` (raw + konversi sparse)

---

### [4] Boot Family (Unpack / Repack)

```
╔══════════════════════════════════════════════╗
║               BOOT FAMILY                  ║
╚══════════════════════════════════════════════╝

[1] Check boot family
[2] Unpack boot/recovery/dtbo
[3] Unpack vendor_boot/init_boot
[4] Unpack vbmeta/vendor_kernel_boot
[5] Repack boot/recovery/dtbo
[6] Repack vendor_boot/init_boot
[7] Repack vbmeta/vendor_kernel_boot
[8] Back
```

#### [1] Check boot family

Scan `input/` dan `temp/img/` untuk mendeteksi boot image yang tersedia:

```
Ditemukan:
  boot.img (128.0 MB) [input]
  vendor_boot.img (64.0 MB) [temp/img]
  dtbo.img (32.0 MB) [input]
```

#### [2] [3] [4] — Unpack

Pilih file boot image untuk di-unpack dengan `magiskboot`. Masing-masing kategori:
- **Kategori 1**: boot.img, recovery.img, dtbo.img
- **Kategori 2**: vendor_boot.img, init_boot.img
- **Kategori 3**: vbmeta.img, vendor_kernel_boot.img

Hasil unpack disimpan di `temp/boot/<type>/`.

#### [5] [6] [7] — Repack

Repack boot image yang sudah di-unpack sebelumnya:
- **Kategori 1**: boot, recovery, dtbo
- **Kategori 2**: vendor_boot, init_boot
- **Kategori 3**: vbmeta, vendor_kernel_boot

Hasil repack disimpan di `temp/boot_out/` dengan nama `*_repack.img`.

---

### [5] Clean Output

```
╔══════════════════════════════════════════════╗
║              CLEAN OUTPUT                  ║
╚══════════════════════════════════════════════╝

Pilih folder yang ingin dibersihkan:

  [1] img/       (15.2 GB)
  [2] contents/  (4.5 GB)
  [3] payload/   (6.1 GB)
  [A] Bersihkan SEMUA
  [0] Batal
```

Bersihkan per-subfolder atau semua isi `temp/` sekaligus.

---

### [W] Wizard Mode

Mode wizard akan auto-scan folder dan kasih pilihan tindakan tanpa perlu navigasi menu manual:

```
Scanning for .img files and contents...
  [i] Found 45 .img files
  [i] Found 18 content directories

  [1] Unpack .img files to filesystem contents
  [2] Repack content directories to .img files
  [3] Choose custom folder
  [4] Back
```

#### Opsi 1 — Unpack .img

Pilih sumber .img (dari `input/`, `temp/img/`, `temp/payload/` atau semua), lalu extract filesystem:

```
Choose source:
  [1] input/ (10 files)
  [2] temp/img/ (45 files)
  [3] temp/payload/ (6 files)
  [4] All sources
```

#### Opsi 2 — Repack contents

Pilih direktori yang mau direpack (satu per satu, semua, atau folder kustom):

```
Content directories available:
  [1] mi_ext           [5] product         [9] system_dlkm      [13] vendor
  [2] mi_ext_a         [6] product_a       [10] system_dlkm_a   [14] vendor_a
  [3] odm              [7] system          [11] system_ext      [15] vendor_dlkm
  [4] odm_a            [8] system_a        [12] system_ext_a    [16] vendor_dlkm_a
  [A] All
  [C] Choose custom folder
```

#### Opsi 3 — Custom folder

Masukkan path folder kustom untuk diproses:

```
Enter folder path: /sdcard/Download/my_images

  [1] Unpack .img files in this folder
  [2] Repack subdirectories to .img
  [3] Back
```

---

### [D] Debug Mode

Tekan `D` di menu utama untuk toggle mode debug ON/OFF:

```
Select Menu : D
[V] Debug mode: ON
```

Saat ON, semua operasi menampilkan info detail:
- **Unpack filesystem**: deteksi tipe (erofs/ext4), skip firmware
- **Repack filesystem**: perintah mkfs yang dijalankan, ref_img yang dipakai
- **Super unpack**: parameter lpunpack, sparse detection
- **Payload extract**: file .img yang ditemukan
- **Repack loop**: direktori diproses, status src_img

---

## Fitur Baru v2.0.2

### Firmware Skip (42 partisi otomatis dilewati)

Partisi firmware/bootloader berikut otomatis di-skip saat extract/repack filesystem karena bukan filesystem yang bisa diekstrak:

```
abl, aop, aop_config, bluetooth, boot, countrycode, cpucp, cpucp_dtb,
devcfg, dsp, dtbo, featenabler, hyp, idmanager, imagefv, init_boot,
keymaster, modem, modemfirmware, multiimgqti, pvmfw, qupfw, recovery,
shrm, slim_audiop, soccp_dcd, soccp_debug, spuservice, storage, tz,
uefi, uefisecapp, vbmeta, vbmeta_system, vbmeta_vendor, vendor_boot,
vendor_kernel_boot, vm-bootsys, xbl, xbl_config, xbl_ramdump, xm_edid
```

### Multi-Chunk Sparse (>4GB)

`raw_to_sparse` sekarang support image >4GB (seperti `product.img` hingga 5GB+). Data otomatis dipecah menjadi beberapa RAW chunk agar muat dalam format Android sparse:

```
[INFO] Image besar (4.8GB), split jadi 2 RAW chunks
[INFO] Sparse multi-chunk selesai: 2 chunks
```

### Hasil Repack — Penamaan Spesifik

Semua hasil repack diberi akhiran `_repack.img` agar mudah dikenali:

| Operasi | Output |
|---------|--------|
| Repack super.img | `temp/repacked/super_repack.img` |
| Repack boot.img | `temp/boot_out/boot_repack.img` |
| Repack vendor_boot.img | `temp/boot_out/vendor_boot_repack.img` |
| Repack system.img | `temp/img/system_repack.img` |
| Repack vendor.img | `temp/img/vendor_repack.img` |
| Repack product.img | `temp/img/product_repack.img` |

---

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
| `lucky-arch` | ⬜ Opsional | Unpack super.img (satu binary, gantikan lpunpack + simg2img, hemat storage) |
| `lpunpack` | ⬜ Opsional* | Unpack super.img (tidak wajib jika lucky-arch ada) |
| `simg2img` | ⬜ Opsional* | Konversi sparse ke raw (tidak wajib jika lucky-arch ada) |
| `extract.erofs` | ✅ Wajib | Extract EROFS |
| `debugfs` | ✅ Wajib | Extract ext4 |
| `magiskboot` | ✅ Wajib | Unpack/repack boot (7 tipe) |
| `lpmake` | ⬜ Opsional | Repack super.img (sparse) |
| `mkfs.erofs` | ⬜ Opsional | Repack EROFS (+ sparse) |
| `make_ext4fs` | ⬜ Opsional | Repack ext4 (built-in sparse) |

## Catatan Rilis

### v2.0.2 (2026-06-12)

[!] Perbaikan Bug:
- Fix `raw_to_sparse` struct.pack format mismatch — konversi sparse sekarang benar
- Fix `raw_to_sparse` uint32 overflow — support multi-chunk RAW untuk image >4GB (misal product.img 4.8GB)
- Fix **stray "continue"** di main.py repack loop — semua direktori ke-skip karena `continue` tanpa kondisi → repack selalu "Semua gagal"
- Fix **"Semua filesystem gagal direpack"** — direktori ext4 berisi subfolder `ext4_extract/`, file tidak langsung di root folder
- Fix **SIGSYS crash** — 42 partisi non-filesystem (abl, aop, modem, tz, xbl, dll) sekarang di-skip dengan pesan jelas

[+] Fitur Baru:
- **Wizard mode [W]** — Auto-scan folder untuk .img & content directories, pilih unpack/repack + path kustom
- **Debug mode [D]** — Toggle global, semua module tampilkan info detail proses
- **Firmware skip** — 42 partisi firmware/bootloader otomatis dilewati

[*] Peningkatan:
- Output konsisten — unpack_filesystem bersihkan folder sebelum ekstrak ulang
- Error handling — cleanup dengan rmtree pada partial/failed extraction
- DEBUG flag global di `modules/common.py` — bisa diakses semua module
- Menu boot sekarang 3 kategori dengan sub-menu spesifik

### v2.0.1 (2026-06-09)

[!] Perbaikan Bug:
- Fix `vendor_boot.img` unpack — exit code 3 (`vendor_boot` detected) BUKAN error
- Fix boot unpack — file sumber tidak dihapus setelah unpack (diperlukan untuk repack)
- Fix repack boot — source image tidak ditemukan di work_dir

[+] Fitur Baru:
- **6 tipe boot** — boot, recovery, dtbo, vendor_boot, init_boot, vbmeta, vendor_kernel_boot
- Repack sparse — hasil repack filesystem otomatis di-sparse-kan
- Penamaan repack jelas — `*_repack.img` untuk semua hasil repack
- Menu boot dirombak — 3 kategori dengan sub-menu repack spesifik

## Kredit

- **Developer**: soe1hom-arch / Wandi
- **payload-dumper-go**: ssut
- **lucky-arch**: soe1hom-arch (penggabungan simg2img + lpunpack)
- **lpunpack / lpmake / simg2img**: AOSP
- **extract.erofs / mkfs.erofs**: erofs-utils (NDK by sekaiacg)
- **debugfs**: e2fsprogs (Tsurugi Linux)
- **make_ext4fs**: rendiix
- **magiskboot**: topjohnwu (Magisk)

## Lisensi

MIT License — lihat `LICENSE` untuk detail.
