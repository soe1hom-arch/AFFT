#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="soe1hom-arch/android-firmware-toolkit"
TAG="v2.1.1-full"
ZIP_NAME="AFT_TOLLS-v2.1.1-full.zip"
WORKDIR="$HOME/android-firmware-toolkit"
TMPDIR="$(mktemp -d)"
ARCHIVE="$TMPDIR/$ZIP_NAME"

pkg update -y
pkg install -y curl unzip python
termux-setup-storage || true

mkdir -p "$WORKDIR"
cd "$TMPDIR"
curl -fL "https://github.com/$REPO/releases/download/$TAG/$ZIP_NAME" -o "$ARCHIVE"
unzip -q "$ARCHIVE" -d "$WORKDIR"
cd "$WORKDIR/AFT_TOLLS"

chmod +x main.py bin/* 2>/dev/null || true

cat <<EOF
Installed to: $WORKDIR/AFT_TOLLS

Run:
  cd $WORKDIR/AFT_TOLLS
  python main.py
EOF
