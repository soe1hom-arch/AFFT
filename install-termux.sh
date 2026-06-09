#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="soe1hom-arch/AFFT"
TAG="v2.0.1"
ZIP_NAME="AFFT-v2.0.1-full.zip"
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
pkg install -y wget unzip python
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
echo "Downloading AFFT v2.0.1..."
wget -q --show-progress "https://github.com/$REPO/releases/download/$TAG/$ZIP_NAME" -O "$ARCHIVE"
unzip -q "$ARCHIVE" -d "$WORKDIR"
cd "$WORKDIR/AFFT"

chmod +x main.py bin/* 2>/dev/null || true

# Buat perintah "afft" biar bisa dipanggil dari mana aja
cat > "$PREFIX/bin/afft" << 'WRAPPER'
#!/data/data/com.termux/files/usr/bin/bash
cd "$WORKDIR/AFFT"
exec python main.py "$@"
WRAPPER
chmod +x "$PREFIX/bin/afft"



echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  AFFT v2.0.1 installed!                       ║"
echo "║                                              ║"
echo "║  Run:                                        ║"
echo "║    cd $WORKDIR/AFFT                          ║"
echo "║    python main.py                            ║"
echo "║                                              ║"
echo "║  Place firmware in: input/                   ║"
echo "║  Results in:       temp/img/, temp/contents/ ║"
echo "╚══════════════════════════════════════════════╝"
