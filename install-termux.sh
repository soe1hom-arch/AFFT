#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="soe1hom-arch/android-firmware-toolkit"
TAG="v2.0"
ZIP_NAME="AFFT-v2.0-full.zip"
WORKDIR="$HOME/android-firmware-toolkit"
TMPDIR="$(mktemp -d)"
ARCHIVE="$TMPDIR/$ZIP_NAME"

clear
cat <<'EOF'
========================================
 Android Firmware Full Toolkit (AFFT)
========================================
Installer for Termux
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

if [ -d "$WORKDIR/AFFT" ]; then
  read -r -p "Existing install found. Replace it? [Y/n] " overwrite
  case "${overwrite:-Y}" in
    n|N)
      echo "Keeping existing install."
      exit 0
      ;;
  esac
  rm -rf "$WORKDIR/AFFT"
fi

mkdir -p "$WORKDIR"
cd "$TMPDIR"
curl -fL "https://github.com/$REPO/releases/download/$TAG/$ZIP_NAME" -o "$ARCHIVE"
unzip -q "$ARCHIVE" -d "$WORKDIR"
cd "$WORKDIR/AFFT"

chmod +x main.py bin/* 2>/dev/null || true

cat <<EOF
========================================
Installed to: $WORKDIR/AFFT

Run:
  cd $WORKDIR/AFFT
  python main.py
EOF
