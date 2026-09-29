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
| **1. Fast Script Installer** | macOS / Linux | `./install.sh` | **Recommended for Mac** (Global `~/.local/bin` link) | Python 3 |
| **2. Windows Batch Installer** | Windows | `install.bat` | **Recommended for Windows** (Checks Python, installs pip packages) | Python 3 |
| **3. Official Homebrew Tap** | macOS / Linux | `brew install omerninyo/tap/rightsub` | **Best for public Mac distribution** | Homebrew |
| **4. Isolated Package (`pipx`)**| Cross-Platform | `pipx install .` | Isolated Python virtual environment | pipx |
| **5. Planned Interactive Wizard**| Cross-Platform | `python setup.py` | Future self-diagnostic & clean-slate setup | [Spec](FUTURE_SETUP_WIZARD.md) |

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
2. **Run the Installer:**
   Double-click `install.bat` (or execute in CMD / PowerShell):
   ```cmd
   install.bat
   ```
3. **Make `rightsub` Available from ANY Directory (Add to PATH):**
   Run this single PowerShell command (as current user, no admin required):
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$((Get-Item .).FullName)", "User")
   ```
   Open a new CMD or PowerShell window and test:
   ```cmd
   rightsub auto "C:\Movies\Gladiator.mkv"
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

## 🔮 Future Roadmap: Interactive Setup Wizard
For technical details on the planned autonomous onboarding wizard, see [Architectural Specification: Automated Setup & Health-Check Wizard](FUTURE_SETUP_WIZARD.md).
