# 📦 Global Installation & Distribution Guide — RightSub

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="INSTALLATION_GUIDE.he.md"><b>עברית</b></a>
</p>

This guide explains how to install **RightSub** as a global command-line tool across **macOS**, **Windows**, and **Linux**, allowing you to invoke `rightsub` from any terminal or command prompt directory.

---

## 🧭 Installation Methods Comparison

| Method | Operating System | Command | Best For | Prerequisites |
| :--- | :--- | :--- | :--- | :---: |
| **1. Official Homebrew Tap** | macOS / Linux | `brew tap omerninyo/tap && brew install rightsub` | **Recommended for macOS** (1-sec universal bottle) | Homebrew |
| **2. Fast Script Installer** | macOS / Linux | `./install.sh` | Local developer setup (Global `~/.local/bin` link) | Python 3 |
| **3. Windows Batch Installer** | Windows | `install.bat` | **Recommended for Windows** (Checks Python, installs packages & auto-updates User PATH) | Python 3 |
| **4. Isolated Package (`pipx`)**| Cross-Platform | `pipx install .` | Isolated Python virtual environment | pipx |
| **5. Setup, Hooks & Diagnostics**| Cross-Platform | `rightsub setup` / `rightsub doctor` | End-to-end onboarding wizard, downloader hooks, services & health check | RightSub installed |
| **6. AI Agent MCP Auto-Installer**| Cross-Platform | `rightsub mcp --install` | 1-click native MCP Server registration for Antigravity, Claude, Cursor & Windsurf | RightSub installed |

---

## 🐣 Starting from Scratch (Clean-Slate / Bare System)

If you are setting up RightSub on a brand new computer lacking common developer tools:

### macOS without Homebrew:
1. **Install Homebrew** (The standard macOS package manager):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **Install FFmpeg and Python** (1 command):
   ```bash
   brew install ffmpeg python
   ```
   *(Alternative without Homebrew: Download the official Python installer from [python.org](https://www.python.org/downloads/macos/) and a static FFmpeg build from [evermeet.cx/ffmpeg/](https://evermeet.cx/ffmpeg/)).*

### Windows without Winget or Python:
1. **Install Python 3.9+**:
   - Download the official installer from [python.org/downloads/windows](https://www.python.org/downloads/windows/).
   - ⚠️ **CRITICAL STEP**: On the first installer screen, check the box:  
     ☑ **"Add python.exe to PATH"**.
2. **Install FFmpeg**:
   - If Windows Package Manager is available:
     ```cmd
     winget install Gyan.FFmpeg
     ```
   - If Winget is not installed: Download the release build archive from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and extract `ffmpeg.exe` directly into your RightSub folder.

---

## ⚡ Method 1: Fast macOS & Linux Installer (`install.sh`)

The [install.sh](file:///Volumes/Other/Antigravity/RightSub/install.sh) script verifies dependencies (`python3`, `ffmpeg`), installs packages from `requirements.txt`, and creates a global symlink in `~/.local/bin/rightsub`.

### Local Installation:
```bash
git clone https://github.com/omerninyo/RightSub.git
cd RightSub
./install.sh
```

### Remote One-Liner on Any Machine:
```bash
curl -fsSL https://raw.githubusercontent.com/omerninyo/RightSub/main/install.sh | bash
```

### Verification:
```bash
rightsub --help
```

### Uninstallation:
```bash
./install.sh --uninstall
```

---

## 🪟 Method 2: Windows Installation (`install.bat`)

1. **Clone or Download the Repository:**
   ```cmd
   git clone https://github.com/omerninyo/RightSub.git
   cd RightSub
   ```
2. **Run the Installer (Automatically Registers Global `PATH`):**
   Double-click `install.bat` (or execute in CMD / PowerShell):
   ```cmd
   install.bat
   ```
   `install.bat` verifies `python` and `ffmpeg`, installs dependencies from `requirements.txt`, and **automatically registers the RightSub directory in your Windows User `PATH`** via PowerShell (no Administrator privileges required).
3. **Verify & Launch:**
   Open a new CMD or PowerShell window and run:
   ```cmd
   rightsub          :: Launches the Interactive Mastering Wizard
   rightsub setup    :: Runs the First-Time Setup & Hooks Wizard
   rightsub auto "C:\Movies\Gladiator.mkv"
   ```
   *(Manual PATH fallback if PowerShell execution is restricted on your system:)*
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$((Get-Item .).FullName)", "User")
   ```

---

## 🍺 Method 3: Official Homebrew Tap (`brew install`)

For macOS users who prefer Homebrew package management:
The formula is pre-built in [Formula/rightsub.rb](file:///Volumes/Other/Antigravity/RightSub/Formula/rightsub.rb).

```bash
brew tap omerninyo/tap
brew trust omerninyo/tap  # Required on Homebrew 7.0+ for external taps
brew install rightsub
```

Alternatively, you can install directly in a single command:
```bash
brew install omerninyo/tap/rightsub
```

Homebrew automatically manages `ffmpeg` and `python` dependencies, creates a virtualenv in `/opt/homebrew/Cellar/rightsub/`, and symlinks the binary directly to `/opt/homebrew/bin/rightsub`.

---

## 🐍 Method 4: Isolated Python Package via `pipx`

For isolated Python environments without polluting the system Python:

```bash
# If pipx is not installed:
# macOS: brew install pipx && pipx ensurepath
# Windows: py -m pip install pipx && py -m pipx ensurepath

# Install from cloned folder:
cd RightSub
pipx install .

# Or install directly from GitHub:
pipx install git+https://github.com/omerninyo/RightSub.git
```

---

## ⚙️ PATH Troubleshooting

### macOS & Linux:
If `./install.sh` succeeded but running `rightsub` returns `command not found`, ensure that `~/.local/bin` is in your active shell `PATH`:
1. Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
2. Reload your shell:
   ```bash
   source ~/.zshrc
   ```

### Windows:
If typing `rightsub` in Command Prompt returns `'rightsub' is not recognized`:
1. Press `Win + R`, type `sysdm.cpl`, press Enter.
2. Go to **Advanced** -> **Environment Variables**.
3. Under **User variables**, select `Path` -> **Edit** -> **New**.
4. Paste the full folder path to your RightSub directory (e.g. `C:\Tools\RightSub`).
5. Click **OK** and reopen Command Prompt.

---

## 🧙 Post-Install Onboarding: Setup Wizard, Interactive TUI & MCP Server (`v1.5.0`)

Once RightSub is installed, three built-in interactive wizards let you configure, operate, and connect RightSub without memorizing any flags:

1. **First-Time Setup, Downloader Hooks & Background Service Wizard (`rightsub setup`):**
   ```bash
   rightsub setup
   ```
   Runs a full system diagnostic (`rightsub doctor`), optionally configures `TMDB_API_KEY` and `GEMINI_API_KEY` (`~/.config/rightsub/config.json` with `chmod 600`), generates ready-to-use `qBittorrent` / `Transmission` completion hooks (`--install-hooks`), registers live Sonarr/Radarr webhooks, and optionally installs `rightsub serve` as a background OS service (`launchd` on macOS, `systemd --user` on Linux, `schtasks` on Windows via `--install-service`).
2. **Interactive Terminal & Windows CMD Mastering Wizard (`rightsub`):**
   ```bash
   rightsub
   ```
   Running `rightsub` with no arguments in any interactive terminal opens a numbered menu with Drag & Drop path normalization and a built-in terminal file browser (`[B] Browse`).
3. **1-Click Native MCP Server Registration for AI Agents (`rightsub mcp --install`):**
   ```bash
   rightsub mcp --install
   ```
   Automatically registers RightSub's local JSON-RPC 2.0 MCP Server (`8` tools) into **Google Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf**, and **Claude Code**.

For architectural details, see [RFC 001: Interactive CLI Wizard](proposals/RFC_001_INTERACTIVE_TUI.md), [RFC 002: Native MCP Server](proposals/RFC_002_MCP_SERVER.md), [RFC 003: Setup & Health-Check Wizard](proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.md), and the [Product Roadmap](../ROADMAP.md).
