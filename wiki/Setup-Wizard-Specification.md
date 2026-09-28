# 🔮 Architectural Specification: Automated Setup & Health-Check Wizard

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="FUTURE_SETUP_WIZARD.he.md"><b>עברית</b></a>
</p>

This document details the architectural design principles, workflow, and edge-case handling for a future **Interactive Setup & Health-Check Wizard** for **RightSub**.  
The wizard's primary objective is to make onboarding 100% autonomous (One-Click / One-Liner), **even on a completely bare, clean-slate computer** lacking common developer tools (such as macOS machines without Homebrew, or Windows PCs without Winget or pre-installed Python).

---

## 1. Core Principles & Goals

1. **Zero Manual Prerequisites:**
   Users should never need to look up external tutorials, edit operating system environment variables, or know how to configure PATH variables manually.
2. **Clean-Slate Resilience:**
   - **macOS without Homebrew:** The wizard detects missing package managers and offers either a guided 1-click Homebrew installation or direct static binary downloads requiring no package manager.
   - **Windows without Winget or Python:** The wizard provides clear direct commands, silent installation scripts with `PrependPath=1`, or automated fallback downloads.
3. **Automated PATH Injection:**
   Upon setup completion, `rightsub` is guaranteed to be available globally from any open terminal window without manual configuration.
4. **Self-Diagnostic "Doctor" Mode:**
   Provides an end-to-end diagnostic report covering Python 3, FFmpeg, TMDb API keys, Ollama local daemon, and Quicksubs.

---

## 2. Bare-System Handling Matrix

| Scenario | macOS (No Homebrew installed) | Windows (No Winget or Python installed) |
| :--- | :--- | :--- |
| **Detection** | `which brew` returns exit code 1. | `winget` or `python` commands unrecognized in command prompt. |
| **Recommended Path (Automated)** | Wizard offers to run official Homebrew bootstrap: <br>`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | If Python is missing: automated silent download with `PrependPath=1`.<br>If Winget exists: `winget install Gyan.FFmpeg`. |
| **Standalone Path (Zero Package Managers)** | Direct `curl` download of pre-compiled, verified static `ffmpeg` binary directly into RightSub's local folder (no sudo or package managers required). | PowerShell download of official Gyan.FFmpeg release archive with automatic extraction of `ffmpeg.exe` directly into the RightSub folder. |

---

## 3. Interactive Wizard Flow (`rightsub setup` / `python setup.py`)

```text
==================================================================
           RightSub — Environment Setup & Health Wizard
==================================================================

[1/5] Checking Operating System & Architecture...
      ✓ Detected: macOS 15.1 (Apple Silicon - aarch64)

[2/5] Checking Python Runtime...
      ✓ Python 3.9+ detected: /opt/homebrew/bin/python3 (v3.11.8)
      ✓ Installing/verifying requirements.txt dependencies... Done.

[3/5] Checking Media Binaries & Package Managers...
      [!] Homebrew is not installed on this Mac.
          How would you like to install FFmpeg?
          > 1. Install Homebrew and FFmpeg automatically (Recommended)
            2. Download standalone FFmpeg binary directly (No package manager needed)
            3. I will install FFmpeg manually later

[4/5] Configuring Global System PATH...
      ✓ Adding ~/.local/bin to active shell profile (~/.zshrc)... Done.
      ✓ Global command 'rightsub' is now active from ANY terminal.

[5/5] Service Onboarding & Secrets (Optional):
      [?] Enter your TMDb API Key (or press Enter to skip):
          > ****************************************
          ✓ TMDb API Key validated via live ping (HTTP 200). Saved to ~/.config/rightsub/config.json.
      
      [?] Ollama Local AI Status:
          ✓ Detected Ollama daemon at http://localhost:11434
          ✓ Installed models: llama3.2:latest, qwen2.5:7b

==================================================================
[✓] RightSub is 100% ready to use!
    Try running: rightsub auto "MyMovie.mkv"
==================================================================
```

---

## 4. Automated PATH Registration

### macOS & Linux:
The wizard reads the user's active shell from `$SHELL`:
1. If Zsh: inspects `~/.zshrc`.
2. If Bash: inspects `~/.bashrc` or `~/.bash_profile`.
3. If `~/.local/bin` is not yet exported: automatically appends:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
4. Creates executable symlink (`ln -sf`) from `rightsub.py` to `~/.local/bin/rightsub`.

### Windows:
Rather than requiring the user to navigate the Windows System Properties GUI, the wizard executes a PowerShell command updating the Windows User Environment Registry directly:
```powershell
$installDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
    Write-Host "[✓] RightSub successfully added to User PATH permanently."
}
```

---

## 5. Diagnostic Health-Check Command (`rightsub doctor`)

The same underlying verification engine will power an autonomous diagnostic tool:
```bash
rightsub doctor
```
This command inspects all system dependencies, prints a clear status dashboard (Python, FFmpeg, Ollama, TMDb, PATH), and offers 1-click self-repair for any missing components.
