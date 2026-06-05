#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="soe1hom-arch/android-firmware-toolkit"
TAG="v2.1.2-full"
ZIP_NAME="AFT_TOLLS-v2.1.2-full.zip"
WORKDIR="$HOME/android-firmware-toolkit"
TMPDIR="$(mktemp -d)"
ARCHIVE="$TMPDIR/$ZIP_NAME"

clear
cat <<'EOF'
========================================
 Android Firmware Toolkit Installer
========================================
This installs the full package for Termux.
EOF

printf '\nInstall path: %s\n' "$WORKDIR"
read -r -p "Continue with the latest full package? [Y/n] " answer
case "${answer:-Y}" in
  n|N)
    echo "Cancelled."
    exit 0
    ;;
esac

pkg update -y
pkg install -y curl unzip python
termux-setup-storage || true

if [ -d "$WORKDIR/AFT_TOLLS" ]; then
  read -r -p "Existing install found. Replace it? [Y/n] " overwrite
  case "${overwrite:-Y}" in
    n|N)
      echo "Keeping existing install."
      exit 0
      ;;
  esac
  rm -rf "$WORKDIR/AFT_TOLLS"
fi

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
