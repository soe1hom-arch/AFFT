# Android Firmware Toolkit

Android Firmware Toolkit is a lightweight Termux-friendly toolkit for extracting modern Android firmware images on-device.

Version: `v2.1`

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

## Included Binaries

The following tools are bundled in `bin/` for convenience:

- `payload-dumper-go`
- `lpunpack`
- `simg2img`
- `extract.erofs`
- `debugfs`

These binaries are included to support Android firmware extraction workflows. Each tool belongs to its respective upstream project.

## Usage

1. Place your firmware or image file inside the `input/` folder.
2. Run the toolkit:

```bash
python main.py
```

3. Select the extraction mode from the menu.
4. Check the extracted files inside the `output/` folder.

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
- Bundled binaries: respective upstream authors and projects

## Notes

- The toolkit copies its helper binaries into the home directory at runtime.
- Some images are treated as EROFS partitions and others as EXT4 partitions based on filename rules in `main.py`.
- Make sure you trust the source of any firmware image before extracting or executing any bundled binary.

## License

No explicit license file is included in this archive. Add one before publishing publicly on GitHub if you want a clear reuse policy.
