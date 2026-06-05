# Android Firmware Toolkit

Android Firmware Toolkit is a lightweight Termux-friendly toolkit for extracting modern Android firmware images on-device.

Version: `v2.1.1`

## Overview

This project helps unpack common Android firmware packages and filesystem images used on Android 12 to Android 15, including HyperOS-based builds.

Supported workflows:

- `payload.bin` extraction
- `super.img` unpacking
- `system.img`, `vendor.img`, `product.img`, and related filesystem image extraction
- Sparse image conversion
- EROFS and EXT4 extraction

## Features

- One-click extraction workflow
- Automatic sparse image detection
- Automatic sparse-to-raw conversion
- Filesystem detection for supported partitions
- Continuous menu loop
- Output folder management
- Termux-compatible command flow

## Requirements

- Termux
- Python 3
- Storage access for the input and output folders

Recommended setup in Termux:

```bash
pkg update -y
pkg install python -y
termux-setup-storage
```

## Project Structure

```text
AFT_TOLLS/
├── main.py
├── bin/
├── input/
├── output/
├── temp/
├── logs/
```

## Binary Policy

This repository is intentionally source-only.

The helper binaries previously bundled with the toolkit are not tracked in the
repository anymore to keep redistribution safer from a licensing perspective.
If you build your own package, add the compatible helper binaries to `bin/`
before running the script.

Expected helper filenames:

- `payload-dumper-go`
- `lpunpack`
- `simg2img`
- `extract.erofs`
- `debugfs`

## Usage

1. Place your firmware or image file inside the `input/` folder.
2. Run the toolkit:

```bash
python main.py
```

3. Select the extraction mode from the menu.
4. Check the extracted files inside the `output/` folder.

## Quick Start For Beginners

If you do not want to set up the project manually, use the latest GitHub Release source package and add the helper binaries separately.

1. Download the latest source release ZIP.
2. Extract it on your device.
3. Open Termux in the extracted folder.
4. Run:

```bash
pkg update -y
pkg install python -y
termux-setup-storage
python main.py
```

5. Place the required helper binaries in `bin/` if they are not already present.

### One-line Termux Installer

If you want the full package instead of the source-only repo, run:

```bash
pkg update -y && pkg install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/soe1hom-arch/android-firmware-toolkit/main/install-termux.sh)
```

This installs the latest full package into `~/android-firmware-toolkit/AFT_TOLLS`.

## Supported Input Types

- `payload.bin`
- `super.img`
- `system.img`
- `vendor.img`
- `product.img`
- `system_ext.img`
- `vendor_dlkm.img`
- `system_dlkm.img`
- `mi_ext.img`
- `odm.img`

## Credits

- Developer: `soe1hom-arch / Wandi`
- Toolkit concept and workflow: `Android Firmware Toolkit`
- Helper binaries: respective upstream authors and projects

## Notes

- The toolkit copies helper binaries from `bin/` into the home directory at runtime.
- Some images are treated as EROFS partitions and others as EXT4 partitions based on filename rules in `main.py`.
- Make sure you trust the source of any firmware image before extracting or executing any helper binary.

## License

The original project files in this repository are licensed under the MIT License.

See [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for details about helper-binary redistribution notes.
