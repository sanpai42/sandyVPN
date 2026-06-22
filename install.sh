#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="SandyVPN"
LAUNCH_SCRIPT="$APP_DIR/launch.sh"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$DESKTOP_DIR/sandyvpn.desktop"

echo "==> Installing $APP_NAME"
echo "    Location: $APP_DIR"
echo

chmod +x "$APP_DIR/launch.sh"
chmod +x "$APP_DIR/install.sh"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed." >&2
  exit 1
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "Error: python3-tk is not installed." >&2
  echo "Install it with: sudo apt install python3-tk" >&2
  exit 1
fi

echo "==> Setting up Python virtual environment"
if [[ ! -d "$APP_DIR/.venv" ]]; then
  python3 -m venv "$APP_DIR/.venv"
fi

"$APP_DIR/.venv/bin/pip" install --upgrade pip || true

if ! "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"; then
  echo
  echo "Warning: could not install Python packages into .venv."
  if python3 -c "import cryptography, tkinter" 2>/dev/null; then
    echo "System Python already has the required packages."
    echo "launch.sh will use system Python instead."
  else
    echo "Error: missing Python dependencies." >&2
    echo "Try: sudo apt install python3-tk python3-cryptography" >&2
    exit 1
  fi
fi

echo
echo "==> Creating desktop launcher"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=OpenVPN 3 session launcher
Exec=$LAUNCH_SCRIPT
Path=$APP_DIR
Icon=network-vpn
Terminal=false
Categories=Network;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

if [[ -d "$HOME/Desktop" ]]; then
  ln -sf "$DESKTOP_FILE" "$HOME/Desktop/sandyvpn.desktop"
  echo "    Shortcut: $HOME/Desktop/sandyvpn.desktop"
fi

echo "    Menu entry: $DESKTOP_FILE"
echo
echo "Done. You can now:"
echo "  - Double-click launch.sh in this folder"
echo "  - Double-click SandyVPN on your Desktop"
echo "  - Search for SandyVPN in your application menu"
echo
echo "First time only: if your file manager asks, choose"
echo "\"Run\" or \"Allow executing file as program\" for launch.sh."
