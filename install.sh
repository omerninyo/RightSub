#!/usr/bin/env bash
# ==============================================================================
# RightSub Installer for macOS & Linux
# Installs 'rightsub' as a global command in ~/.local/bin or /usr/local/bin
# ==============================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_NAME="rightsub"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== RightSub Global CLI Installer ===${NC}"

# Handle uninstall
if [ "$1" == "--uninstall" ] || [ "$1" == "-u" ]; then
    echo -e "${YELLOW}[*] Uninstalling RightSub global CLI link...${NC}"
    REMOVED=0
    for TARGET_DIR in "$HOME/.local/bin" "/usr/local/bin"; do
        if [ -L "$TARGET_DIR/$BIN_NAME" ] || [ -f "$TARGET_DIR/$BIN_NAME" ]; then
            rm -f "$TARGET_DIR/$BIN_NAME"
            echo -e "${GREEN}[✓] Removed: $TARGET_DIR/$BIN_NAME${NC}"
            REMOVED=1
        fi
    done
    if [ $REMOVED -eq 0 ]; then
        echo -e "[i] No global RightSub link found."
    fi
    echo -e "${GREEN}[✓] Uninstallation complete.${NC}"
    exit 0
fi

# 1. Check Python 3
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[-] Error: python3 is not installed or not in PATH.${NC}"
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python detected: $(python3 --version) (${PY_VERSION})${NC}"

# 2. Check FFmpeg (Warning if missing)
if ! command -v ffmpeg &>/dev/null; then
    echo -e "${YELLOW}[!] Warning: ffmpeg is not installed.${NC}"
    if command -v brew &>/dev/null; then
        echo -e "${YELLOW}[!] To install FFmpeg on macOS, run: brew install ffmpeg${NC}"
    else
        echo -e "${YELLOW}[!] Please install ffmpeg using your system package manager.${NC}"
    fi
else
    echo -e "${GREEN}[✓] FFmpeg detected: $(ffmpeg -version | head -n 1 | awk '{print $1, $2, $3}')${NC}"
fi

# 3. Install Python dependencies
echo -e "${BLUE}[*] Verifying/installing Python dependencies from requirements.txt...${NC}"
if [ -f "$REPO_DIR/requirements.txt" ]; then
    python3 -m pip install -q -r "$REPO_DIR/requirements.txt" --user || python3 -m pip install -q -r "$REPO_DIR/requirements.txt"
    echo -e "${GREEN}[✓] Python dependencies installed successfully.${NC}"
fi

# 4. Make rightsub.py executable
chmod +x "$REPO_DIR/rightsub.py"
if [ -L "$REPO_DIR/rightsub" ]; then
    chmod +x "$REPO_DIR/rightsub"
fi

# 5. Determine target installation directory in PATH
INSTALL_DIR=""
if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    INSTALL_DIR="$HOME/.local/bin"
elif [[ ":$PATH:" == *":/usr/local/bin:"* ]] && [ -w "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
fi

mkdir -p "$INSTALL_DIR"
TARGET_LINK="$INSTALL_DIR/$BIN_NAME"

# Create symlink
rm -f "$TARGET_LINK"
ln -sf "$REPO_DIR/rightsub.py" "$TARGET_LINK"
echo -e "${GREEN}[✓] Created global executable link: ${TARGET_LINK} -> ${REPO_DIR}/rightsub.py${NC}"

# 6. Verify PATH availability
if command -v "$BIN_NAME" &>/dev/null; then
    RESOLVED_PATH=$(which "$BIN_NAME")
    echo -e "${GREEN}==================================================================${NC}"
    echo -e "${GREEN}[✓] SUCCESS: RightSub is now installed globally!${NC}"
    echo -e "    Binary location: ${RESOLVED_PATH}"
    echo -e "    You can now run 'rightsub' directly from ANY directory in terminal."
    echo -e "    Try running: rightsub --help"
    echo -e "${GREEN}==================================================================${NC}"
else
    echo -e "${YELLOW}==================================================================${NC}"
    echo -e "${YELLOW}[!] Note: '${INSTALL_DIR}' is not currently in your active PATH.${NC}"
    echo -e "    To add it permanently, add the following line to your ~/.zshrc or ~/.bashrc:"
    echo -e "    export PATH=\"${INSTALL_DIR}:\$PATH\""
    echo -e "    Then reload your shell: source ~/.zshrc"
    echo -e "${YELLOW}==================================================================${NC}"
fi
