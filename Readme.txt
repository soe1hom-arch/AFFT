pkg update -y && pkg install python -y && termux-setup-storage

╔══════════════════════════════════════════════╗
║         ANDROID FIRMWARE TOOLKIT            ║
║          By. Wandi | v2.1 (HyperOS)          ║
╚══════════════════════════════════════════════╝


==============================================
LATEST UPDATE (v2.1) - WHAT'S NEW?
==============================================

✓ HyperOS Compatibility Engine:
  Optimasi penuh untuk struktur kompresi firmware Xiaomi HyperOS.

✓ Continuous Menu System (Anti-Keluar):
  Tools tidak otomatis menutup setelah selesai ekstrak. Selesai
  proses, program akan kembali ke menu utama (Looping System).

✓ Updated Binaries Engine:
  Semua binary di folder bin menggunakan versi terbaru (build 2026)
  untuk kestabilan ekstraksi Android 14 / 15 / HyperOS.


==============================================
DESCRIPTION
==============================================

Android Firmware Toolkit adalah tools Termux
untuk mengekstrak firmware Android modern.

Mendukung:

✓ payload.bin
✓ super.img
✓ system/vendor/product.img
✓ EXT4
✓ EROFS
✓ Sparse image
✓ Android 12 / 13 / 14 / 15 / HyperOS


==============================================
FEATURES
==============================================

✓ One Click Extraction
✓ Continuous Menu Loop (New)
✓ Auto Binary Permission
✓ Auto Sparse Convert
✓ Auto Filesystem Detection
✓ EROFS Support
✓ EXT4 Support
✓ Realtime Progress Bar
✓ Output Auto Folder
✓ Termux Compatible


==============================================
FOLDER STRUCTURE
==============================================

project/

├── main.py
├── bin/
├── input/
├── output/
├── temp/
├── logs/


==============================================
BIN FOLDER
==============================================

Taruh semua binary di folder:

bin/

Binary wajib:

payload-dumper-go
lpunpack
simg2img
extract.erofs
debugfs


==============================================
INPUT FOLDER
==============================================

Taruh firmware/image di folder:

input/

Contoh:

payload.bin
super.img
system.img
vendor.img
product.img


==============================================
SUPPORTED IMG (HYPEROS EXCLUSIVE)
==============================================

Untuk menjaga kestabilan ekstraksi HyperOS, Menu 3
HANYA mendeteksi dan mendukung 8 filesystem berikut:

✓ [1] product.img
✓ [2] vendor_dlkm.img
✓ [3] vendor.img
✓ [4] system.img
✓ [5] system_dlkm.img
✓ [6] system_ext.img
✓ [7] mi_ext.img
✓ [8] odm.img


==============================================
UNSUPPORTED IMG
==============================================

File berikut bukan filesystem biasa:

✗ cust.img (Disabled in v2.0)
✗ abl.img
✗ aop.img
✗ bluetooth.img
✗ boot.img
✗ dtbo.img
✗ dsp.img
✗ hyp.img
✗ modem.img
✗ recovery.img
✗ tz.img
✗ vbmeta.img
✗ xbl.img

File di atas biasanya:

- bootloader
- firmware
- kernel
- modem
- metadata

dan bukan file system Android.


==============================================
MENU EXPLANATION
==============================================

[1] Extract payload.bin

Digunakan untuk OTA ROM.

Output:

system.img
vendor.img
product.img
dll


----------------------------------------------

[2] Unpack super.img

Digunakan untuk Fastboot ROM.

Output:

system.img
vendor.img
product.img
dll


----------------------------------------------

[3] Extract IMG

Digunakan untuk extract filesystem Android.

Contoh:

system.img
vendor.img
product.img

Output:

app/
bin/
lib64/
system/
vendor/
dll


----------------------------------------------

[4] Clean output folder

Menghapus isi folder output dan temp.


----------------------------------------------

[5] Exit

Keluar dari program.


==============================================
HOW TO USE
==============================================

1. Taruh file di folder input/

2. Jalankan:

python main.py

3. Pilih menu

4. Hasil extract ada di:

output/


==============================================
WORKFLOW OTA ROM
==============================================

payload.bin
↓
Menu 1
↓
system.img
↓
Menu 3
↓
Android filesystem


==============================================
WORKFLOW FASTBOOT ROM
==============================================

super.img
↓
Menu 2
↓
system.img
↓
Menu 3
↓
Android filesystem


==============================================
NOTES
==============================================

✓ Jangan extract super.img di Menu 3

✓ Menu 3 hanya untuk filesystem image

✓ EROFS modern Android 14/15 & HyperOS didukung

✓ Sparse image otomatis dikonversi

✓ Semua binary otomatis chmod executable


==============================================
TESTED ON
==============================================

✓ Termux
✓ Android 12
✓ Android 13
✓ Android 14
✓ Android 15
✓ Xiaomi HyperOS 1.0 & 2.0


==============================================
CREDITS
==============================================

payload-dumper-go
lpunpack
simg2img
extract.erofs
debugfs

All credits belong to original developers.
This project only combines existing tools
into one Termux utility.


==============================================
AUTHOR
==============================================

By. Wandi
