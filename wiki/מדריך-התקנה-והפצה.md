<div dir="rtl">

# 📦 מדריך התקנה גלובלית והפצה — RightSub

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="INSTALLATION_GUIDE.md"><b>English</b></a>
</p>

מדריך זה מסביר כיצד להתקין את **RightSub** כפקודת מערכת גלובלית ב-**macOS**, **Windows** וב-**Linux**, כך שתוכלו להקליד `rightsub` ישירות מכל חלון טרמינל או שורת פקודה (CMD/PowerShell) ובכל תיקייה במחשב.

---

## 🧭 השוואת שיטות ההתקנה

| שיטה | מערכת הפעלה | פקודת ההתקנה | מתי להשתמש? | דרישות קדם |
| :--- | :--- | :--- | :--- | :---: |
| **1. חבילת Homebrew Tap רשמית** | macOS / Linux | `brew tap omerninyo/tap && brew install rightsub` | **הכי מומלץ למשתמשי Mac** (בקבוק אוניברסלי בשנייה אחת) | Homebrew |
| **2. סקריפט התקנה מהיר** | macOS / Linux | `./install.sh` | התקנה מקומית למפתחים (קישור גלובלי ב-`~/.local/bin`) | Python 3 |
| **3. מתקין חלונות Batch** | Windows | `install.bat` | **הכי מומלץ למשתמשי Windows** (בודק Python, מתקין ספריות ומזריק ל-PATH אוטומטית) | Python 3 |
| **4. חבילת Python מבודדת (`pipx`)** | חוצה-פלטפורמות | `pipx install .` | סביבת פייתון מבודדת ונקייה | pipx |
| **5. אשף התקנה, Hooks ואבחון** | חוצה-פלטפורמות | `rightsub setup` / `rightsub doctor` | אשף הקמה ראשונית, יצירת Hooks ל-qBittorrent/Sonarr, שירות רקע ובדיקת בריאות | RightSub מותקן |
| **6. מתקין שרת MCP לסוכני AI** | חוצה-פלטפורמות | `rightsub mcp --install` | רישום אוטומטי בלחיצה אחת ל-Antigravity, Claude Desktop, Cursor ו-Windsurf | RightSub מותקן |

---

## 🐣 התקנה מאפס במחשב "ערום" (ללא כלי פיתוח מותקנים)

אם אתם מגדירים את RightSub במחשב נקי לחלוטין שאין עליו כלי פיתוח מוקדמים:

### ב-macOS ללא Homebrew:
1. **התקינו את Homebrew** (מנהל החבילות הסטנדרטי של Mac) בפקודה אחת בטרמינל:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. **התקינו את FFmpeg ואת Python** (בפקודה אחת):
   ```bash
   brew install ffmpeg python
   ```
   *(חלופה ללא Homebrew כלל: הורידו מתקין פייתון רשמי מ-[python.org](https://www.python.org/downloads/macos/) וקובץ בינארי סטטי של FFmpeg מ-[evermeet.cx/ffmpeg/](https://evermeet.cx/ffmpeg/)).*

### ב-Windows ללא Winget וללא Python:
1. **התקנת Python 3.9+**:
   - הורידו את קובץ ההתקנה הרשמי מ-[python.org/downloads/windows](https://www.python.org/downloads/windows/).
   - ⚠️ **שלב קריטי**: במסך ההתקנה הראשון, סמנו ב-V את התיבה:  
     ☑ **"Add python.exe to PATH"**.
2. **התקנת FFmpeg**:
   - אם מותקן אצלכם מנהל החבילות של Windows (Winget):
     ```cmd
     winget install Gyan.FFmpeg
     ```
   - אם אין לכם Winget: הורידו את ארכיון ה-Zip מ-[gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) וחלצו את הקובץ `ffmpeg.exe` ישירות לתוך תיקיית RightSub שלכם.

---

## ⚡ שיטה 1: סקריפט התקנה מהיר ל-macOS ול-Linux (`install.sh`)

סקריפט ההתקנה [install.sh](file:///Volumes/Other/Antigravity/RightSub/install.sh) בודק את קיום התלויות (`python3`, `ffmpeg`), מתקין את הספריות הנדרשות מ-`requirements.txt`, ומייצר קישור הרצה סימבולי גלובלי ב-`~/.local/bin/rightsub`.

### התקנה מקומית מתוך תיקיית המאגר:
```bash
git clone https://github.com/omerninyo/RightSub.git
cd RightSub
./install.sh
```

### התקנה מרחוק במחשב חדש בפקודה אחת:
```bash
curl -fsSL https://raw.githubusercontent.com/omerninyo/RightSub/main/install.sh | bash
```

### בדיקת ההתקנה:
```bash
rightsub --help
```

### הסרת ההתקנה (Uninstall):
```bash
./install.sh --uninstall
```

---

## 🪟 שיטה 2: התקנה ב-Windows (`install.bat`)

1. **הורדה או שכפול המאגר:**
   ```cmd
   git clone https://github.com/omerninyo/RightSub.git
   cd RightSub
   ```
2. **הרצת קובץ ההתקנה (מוסיף ל-`PATH` של המשתמש באופן אוטומטי):**
   לחיצה כפולה על `install.bat` (או הרצתו בחלון CMD / PowerShell):
   ```cmd
   install.bat
   ```
   המתקין בודק את `python` ו-`ffmpeg`, מתקין את הספריות מ-`requirements.txt`, **ורושם אוטומטית את תיקיית RightSub במשתנה ה-`PATH` של המשתמש** באמצעות PowerShell (ללא צורך בהרשאות Administrator).
3. **בדיקה והפעלה מכל תיקייה:**
   פתחו חלון CMD או PowerShell חדש והריצו:
   ```cmd
   rightsub          :: פותח את האשף האינטראקטיבי
   rightsub setup    :: מריץ את אשף ההגדרה הראשונית וה-Hooks
   rightsub auto "C:\Movies\Gladiator.mkv"
   ```
   *(פקודת גיבוי ידנית להוספה ל-PATH אם הרצת PowerShell חסומה במחשבכם:)*
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$((Get-Item .).FullName)", "User")
   ```

---

## 🍺 שיטה 3: חבילת Homebrew Tap רשמית (`brew install`)

למשתמשי Mac המעוניינים בניהול חבילות סטנדרטי:
ההגדרה שמורה בקובץ [Formula/rightsub.rb](file:///Volumes/Other/Antigravity/RightSub/Formula/rightsub.rb).

```bash
brew tap omerninyo/tap
brew trust omerninyo/tap  # נדרש ב-Homebrew 7.0+ לאישור tap צד-שלישי
brew install rightsub
```

או בפקודה ישירה אחת:
```bash
brew install omerninyo/tap/rightsub
```

Homebrew מתקין אוטומטית את תלויות `ffmpeg` ו-`python`, יוצר סביבה מבודדת ב-`/opt/homebrew/Cellar/rightsub/`, ומקשר את הפקודה ל-`/opt/homebrew/bin/rightsub`.

---

## 🐍 שיטה 4: התקנת Python מבודדת באמצעות `pipx`

להתקנה בסביבה נקייה ללא השפעה על הפייתון הראשי של המערכת:

```bash
# אם pipx אינו מותקן:
# ב-macOS: brew install pipx && pipx ensurepath
# ב-Windows: py -m pip install pipx && py -m pipx ensurepath

# התקנה מתוך תיקיית המאגר:
cd RightSub
pipx install .

# או התקנה ישירות מ-GitHub:
pipx install git+https://github.com/omerninyo/RightSub.git
```

---

## ⚙️ פתרון בעיות משתנה ה-PATH

### ב-macOS ו-Linux:
אם ההתקנה הסתיימה בהצלחה אך הקלדת `rightsub` מחזירה `command not found`, ודאו שהנתיב `~/.local/bin` נמצא ב-`PATH`:
1. הוסיפו לפרופיל ה-Shell שלכם (`~/.zshrc` או `~/.bashrc`):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
2. טענו מחדש את הפרופיל:
   ```bash
   source ~/.zshrc
   ```

### ב-Windows:
אם הקלדת `rightsub` בחלון הפקודה מחזירה הודעה שהפקודה אינה מוכרת:
1. לחצו `Win + R`, הקלידו `sysdm.cpl` ולחצו Enter.
2. עברו ללשונית **מתקדם** (Advanced) -> **משתני סביבה** (Environment Variables).
3. תחת **משתני משתמש** (User variables), בחרו ב-`Path` -> **עריכה** (Edit) -> **חדש** (New).
4. הדביקו את הנתיב המלא לתיקיית RightSub (למשל `C:\Tools\RightSub`).
5. אשרו ב-OK ופתחו חלון מסוף חדש.

---

## 🧙 הפעלה ראשונית לאחר ההתקנה: אשף ההגדרות, ממשק אינטראקטיבי ושרת MCP (`v1.5.0`)

מיד לאחר התקנת RightSub, שלושה אשפים מובנים מאפשרים לכם להגדיר, להפעיל ולחבר את המערכת ללא צורך בזכירת דגלים:

1. **אשף הקמה ראשונית, יצירת Hooks ושירות רקע (`rightsub setup`):**
   ```bash
   rightsub setup
   ```
   מבצע בדיקת בריאות מקיפה (`rightsub doctor`), מאפשר הזנת מפתחות אופציונליים (`TMDB_API_KEY`, `GEMINI_API_KEY` בקובץ מוצפן הרשאות `chmod 600` ב-`~/.config/rightsub/config.json`), מייצר אוטומטית סקריפטי סיום הורדה ל-`qBittorrent` ו-`Transmission` (`--install-hooks`), מחבר Webhook חי ל-Sonarr/Radarr, ומאפשר התקנת `rightsub serve` כשירות רקע מערכתי (`launchd` ב-macOS, `systemd --user` ב-Linux, ו-`schtasks` ב-Windows דרך `--install-service`).
2. **אשף הפעלה אינטראקטיבי בטרמינל וב-CMD (`rightsub`):**
   ```bash
   rightsub
   ```
   הקלדת `rightsub` ללא ארגומנטים בכל חלון טרמינל פותחת תפריט ממוספר עם תמיכה בגרירת קבצים (Drag & Drop) ודפדפן קבצים מובנה (`[B] Browse`).
3. **מתקין אוטומטי של שרת MCP לסוכני AI (`rightsub mcp --install`):**
   ```bash
   rightsub mcp --install
   ```
   רושם אוטומטית את שרת ה-MCP המקומי של RightSub (`8` כלים) בתוך **Google Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf** ו-**Claude Code**.

למפרטים הארכיטקטוניים המלאים, ראו [RFC 001: אשף פקודה אינטראקטיבי](proposals/RFC_001_INTERACTIVE_TUI.he.md), [RFC 002: שרת MCP מובנה](proposals/RFC_002_MCP_SERVER.he.md), [RFC 003: אשף התקנה ואבחון](proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.he.md) ו-[מפת הדרכים](../ROADMAP.he.md).

</div>
