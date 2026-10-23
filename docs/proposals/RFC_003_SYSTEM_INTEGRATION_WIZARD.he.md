<div dir="rtl">

# 🛠️ מפרט ארכיטקטוני: אשף התקנה, אבחון, Hooks ושירותי רקע (`rightsub setup` / `rightsub doctor`)

> **סטטוס:** ✅ **שוחרר בייצור (`v1.3.0` ו-`v1.5.0`)** — מומש ב-[`scripts/20_config_and_doctor.py`](file:///Volumes/Other/Antigravity/RightSub/scripts/20_config_and_doctor.py), ב-[`install.sh`](file:///Volumes/Other/Antigravity/RightSub/install.sh), ב-[`install.bat`](file:///Volumes/Other/Antigravity/RightSub/install.bat) וב-[`rightsub.py`](file:///Volumes/Other/Antigravity/RightSub/rightsub.py). מאומת על ידי [`tests/test_config_and_doctor.py`](file:///Volumes/Other/Antigravity/RightSub/tests/test_config_and_doctor.py).

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="RFC_003_SYSTEM_INTEGRATION_WIZARD.md"><b>English</b></a>
</p>

מסמך זה מתעד את עקרונות התכנון, הארכיטקטורה והמימוש בייצור של **אשף ההתקנה, האבחון והחיבור למנהלי הורדות** ב-**RightSub** (`rightsub setup`, `rightsub config`, `rightsub doctor`).  
האשף הופך את תהליך ההתקנה וההגדרה לאוטונומי לחלוטין, כולל הגדרת מפתחות API, יצירת סקריפטי Hook מוכנים ל-`qBittorrent` ו-`Transmission`, חיבור חי ל-`Sonarr`/`Radarr`, ורישום שירות רקע במערכת ההפעלה (`launchd`, `systemd`, `schtasks`).

---

## 1. עקרונות יסוד ומטרות המערכת

1. **אפס דרישות מוקדמות ידניות (Zero Manual Prerequisites):**
   המשתמש אינו נדרש לפתוח מדריכים חיצוניים, לערוך משתני סביבה במערכת ההפעלה, או לדעת כיצד לקנפג את ה-PATH.
2. **התמודדות עם מחשב "ערום" (Bare System Resilience):**
   - **ב-macOS ללא Homebrew:** האשף מזהה שהכלי חסר ומציע התקנה אוטומטית שלו בפקודה מונחית, או הורדה ישירה של בינארי FFmpeg סטטי ללא שום מנהל חבילות.
   - **ב-Windows ללא Winget / ללא Python:** האשף מזהה את הגרסה ומספק פקודת התקנה ישירה או פתיחה ממוקדת של חנות Microsoft Store / הורדה שקטה.
3. **הזרקת PATH אוטומטית (Automated PATH Injection):**
   סיום שלב ההתקנה מבטיח שהפקודה `rightsub` זמינה מכל חלון טרמינל ללא פעולה ידנית מצד המשתמש.
4. **בדיקת בריאות מקיפה (Self-Diagnostic / "Doctor Mode"):**
   בדיקה ויזואלית של כל רכיבי השרשרת: Python, FFmpeg, TMDb API, Ollama ו-Quicksubs.

---

## 2. התמודדות עם תרחישי קצה במחשבים ללא כלי מערכת

| מצב המערכת | macOS (ללא Homebrew) | Windows (ללא Winget / Python) |
| :--- | :--- | :--- |
| **זיהוי החסר** | פקודת `which brew` מחזירה קוד שגיאה. | פקודות `winget` או `python` אינן מוכרות במסוף. |
| **נתיב התקנה מומלץ (אוטומטי)** | האשף מציע להריץ את התקנת Homebrew הרשמית: <br>`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | אם Python חסר: הרצת התקנה שקטה עם דגל `PrependPath=1`.<br>אם Winget קיים: `winget install Gyan.FFmpeg`. |
| **נתיב התקנה עצמאי (ללא שום מנהל חבילות)** | הורדה ישירה (curl) של קובץ בינארי סטטי ומאומת של `ffmpeg` ישירות לתיקיית `~/.local/bin` של RightSub ללא צורך ב-Homebrew או הרשאות מנהל (`sudo`). | הורדה ישירה דרך PowerShell של ארכיון ה-Zip הרשמי מ-gyan.dev וחילוץ `ffmpeg.exe` ישירות לתיקיית RightSub המקומית. |

---

## 3. שלבי פעולת אשף ההתקנה (`rightsub setup` / `python setup.py`)

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

## 4. מנגנון הוספת ה-PATH האוטומטי (Zero Manual Configuration)

### ב-macOS ו-Linux:
האשף מזהה את ה-Shell הפעיל של המשתמש מתוך משתנה הסביבה `$SHELL`:
1. אם ה-Shell הוא Zsh: סורק את הקובץ `~/.zshrc`.
2. אם ה-Shell הוא Bash: סורק את `~/.bashrc` או `~/.bash_profile`.
3. אם הנתיב `~/.local/bin` אינו מוגדר ב-`PATH`: מוסיף אוטומטית שורת ייצוא תקנית:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
4. מייצר קישור סימבולי (`ln -sf`) מ-`rightsub.py` אל `~/.local/bin/rightsub`.

### ב-Windows:
במקום לדרוש מהמשתמש לגשת ללוח הבקרה ולערוך משתני סביבה ידנית, האשף מפעיל פקודת PowerShell המעדכנת ישירות את משתנה הסביבה של המשתמש ברישום המערכת (Windows Registry User Environment):
```powershell
$installDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
    Write-Host "[✓] RightSub successfully added to User PATH permanently."
}
```

---

## 5. הפקודות הזמינות בייצור (`v1.5.0`)

```bash
rightsub setup                    # אשף הקמה מלא: בדיקת מערכת + מפתחות API + יצירת Hooks + שירות רקע
rightsub doctor                   # דשבורד אבחון מערכת מלא (Python, FFmpeg, quicksubs, Ollama, מפתחות API וסוכני MCP)
rightsub config                   # אשף הגדרת מפתחות API שמורים בהרשאות מחמירות (chmod 600)
rightsub config --install-hooks   # יצירת סקריפטי Hook ל-qBittorrent (.sh/.bat) ו-Transmission ב-~/.config/rightsub/hooks/ + רישום Webhook ב-Sonarr/Radarr
rightsub config --install-service # התקנת 'rightsub serve' כשירות רקע מערכתי (launchd ב-macOS / systemd --user ב-Linux / schtasks ב-Windows)
```

</div>
