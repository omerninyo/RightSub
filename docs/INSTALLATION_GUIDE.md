# 📦 Global Installation & Distribution Guide — RightSub

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="INSTALLATION_GUIDE.he.md"><b>עברית</b></a>
</p>

This guide explains how to install **RightSub** as a global command-line executable across macOS and Linux, allowing you to invoke `rightsub` from any terminal directory just like software installed via Homebrew.

---

## 🧭 Installation Methods Comparison

| Method | Command | Best For | Requirements |
| :--- | :--- | :--- | :---: |
| **1. Fast Local Installer (`install.sh`)** | `./install.sh` | **Recommended for your local Mac** (No sudo required) | Python 3 |
| **2. Official Homebrew Tap (`brew`)** | `brew install omerninyo/tap/rightsub` | **Best for public distribution** (Standard macOS package) | Homebrew |
| **3. Isolated Python Tool (`pipx`)** | `pipx install .` | Best for Python developers wanting clean environment isolation | pipx |
| **4. Shell Alias** | `alias rightsub="..."` | Quick temporary solution without symlinks | Zsh / Bash |

---

## ⚡ Method 1: Fast Installer Script (`install.sh`) — Recommended!

The [install.sh](file:///Volumes/Other/Antigravity/RightSub/install.sh) script verifies dependencies (`python3`, `ffmpeg`), installs packages from `requirements.txt`, and creates a global symlink in `~/.local/bin/rightsub`.

### Local Installation:
```bash
cd /Volumes/Other/Antigravity/RightSub
./install.sh
```

### Remote One-Liner on Any Machine:
```bash
curl -fsSL https://raw.githubusercontent.com/omerninyo/RightSub/main/install.sh | bash
```

### Verification:
Open any new terminal window and run:
```bash
rightsub --help
```

### Uninstallation:
```bash
./install.sh --uninstall
```

---

## 🍺 Method 2: Official Homebrew Tap (`brew install`)

Want anyone on macOS to be able to install RightSub using a single `brew` command?  
The formula is pre-built in [Formula/rightsub.rb](file:///Volumes/Other/Antigravity/RightSub/Formula/rightsub.rb).

### Setting Up Your GitHub Tap (One-time setup):

1. **Create a Tap Repository on GitHub:**  
   Create a new public repository named:  
   `homebrew-tap` (under your GitHub account, e.g. `https://github.com/omerninyo/homebrew-tap`).
   > *Note: Homebrew automatically recognizes repositories prefixed with `homebrew-` as custom taps.*

2. **Add the Formula:**  
   Inside your `homebrew-tap` repository, create a directory called `Formula` and copy `Formula/rightsub.rb` into it:  
   `Formula/rightsub.rb`.

3. **Push to GitHub:**  
   Commit and push the formula to GitHub.

### How Users Install via Homebrew:
Users can now install with:
```bash
brew tap omerninyo/tap
brew install rightsub
```
Or in a single command:
```bash
brew install omerninyo/tap/rightsub
```

Homebrew handles `ffmpeg` and `python` dependencies, creates a virtualenv in `/opt/homebrew/Cellar/rightsub/`, and links the binary directly to `/opt/homebrew/bin/rightsub`.

---

## 🐍 Method 3: Isolated Python Package via `pipx`

For isolated Python environments without polluting the system Python:

```bash
# If pipx is not installed:
brew install pipx
pipx ensurepath

# Install from local folder:
cd /Volumes/Other/Antigravity/RightSub
pipx install .

# Or install directly from GitHub:
pipx install git+https://github.com/omerninyo/RightSub.git
```

---

## ⚙️ PATH Troubleshooting

If `./install.sh` succeeded but running `rightsub` returns `command not found`, ensure that `~/.local/bin` is in your active shell `PATH`:

1. Open your shell configuration:
   ```bash
   nano ~/.zshrc
   ```
2. Add the following line at the bottom:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. Save and reload:
   ```bash
   source ~/.zshrc
   ```
