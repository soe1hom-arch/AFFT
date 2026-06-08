#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="soe1hom-arch/AFFT"
TAG="v2.0"
ZIP_NAME="AFFT-v2.0-full.zip"
WORKDIR="$HOME/AFFT"
TMPDIR="$(mktemp -d)"
ARCHIVE="$TMPDIR/$ZIP_NAME"

clear
cat <<'EOF'
╔══════════════════════════════════════════════╗
║   Android Firmware Full Toolkit (AFFT)      ║
║          Termux Installer v2.0              ║
╚══════════════════════════════════════════════╝
EOF

printf '\nInstall path: %s\n' "$WORKDIR"
read -r -p "Continue? [Y/n] " answer
case "${answer:-Y}" in
  n|N)
    echo "Cancelled."
    exit 0
    ;;
esac

pkg update -y
pkg install -y curl unzip python
termux-setup-storage || true

if [ -d "$WORKDIR" ]; then
  read -r -p "Existing install found. Replace it? [Y/n] " overwrite
  case "${overwrite:-Y}" in
    n|N)
      echo "Keeping existing install."
      exit 0
      ;;
  esac
  rm -rf "$WORKDIR"
fi

mkdir -p "$WORKDIR"
cd "$TMPDIR"
echo "Downloading AFFT v2.0..."
curl -fL "https://github.com/$REPO/releases/download/$TAG/$ZIP_NAME" -o "$ARCHIVE"
unzip -q "$ARCHIVE" -d "$WORKDIR"
cd "$WORKDIR/AFFT"

chmod +x main.py bin/* 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  AFFT v2.0 installed!                       ║"
echo "║                                              ║"
echo "║  Run:                                        ║"
echo "║    cd $WORKDIR/AFFT                          ║"
echo "║    python main.py                            ║"
echo "║                                              ║"
echo "║  Place firmware in: input/                   ║"
echo "║  Results in:       temp/img/, temp/contents/ ║"
echo "╚══════════════════════════════════════════════╝"
