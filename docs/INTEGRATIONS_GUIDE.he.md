<div dir="rtl">

# 🔄 מדריך אינטגרציות ואוטומציה לשרתי מדיה (Home Media Integrations)

> **סקירה כללית**: הפעלת RightSub באופן אוטונומי מלא בכל מערך ההורדות והמדיה שלכם בתצורת "הגדר ושכח" (Set-and-Forget). המדריך כולל הגדרות מוכנות להעתקה והדבקה עבור שרתי מדיה ומנהלי הורדות.

המדריך מכסה הגדרות מלאות ומאומתות עבור **Windows** ועבור **macOS/Linux**:
0. [אסטרטגיית 2 הפעימות המומלצת וארכיטקטורת Daemon](#0-אסטרטגיית-2-הפעימות-המומלצת-וארכיטקטורת-daemon)
1. [qBittorrent (הפעלה אוטומטית בסיום הורדה ושמירה על טורנטים)](#1-qbittorrent-הפעלה-בסיום-הורדה-ושמירה-על-שיתוף)
2. [Sonarr ו-Radarr (סקריפטי ייבוא Connect)](#2-sonarr-ו-radarr-סקריפטי-חיבור-connect)
3. [Bazarr (הרצה כ-Post-Processing)](#3-bazarr-עיבוד-והשבחה-לאחר-הורדה)
4. [Transmission (סקריפט סיום הורדה)](#4-transmission-סקריפט-סיום-ב-macoslinux)
5. [Tautulli / Plex (בדיקת מדיה שנוספה לאחרונה)](#5-tautulli--plex-בדיקה-עם-קליטת-מדיה-חדשה)
6. [ניטור תיקיות מקומי עצמאי (ללא תוכנות Arr / עבודה ידנית)](#6-ניטור-תיקיות-מקומי-עצמאי-ללא-תוכנות-arr--העתקה-ידנית)
7. [אימות ובדיקת פעולה (Troubleshooting)](#7-אימות-ובדיקת-פעולה-troubleshooting)

---

## 0. אסטרטגיית 2 הפעימות המומלצת וארכיטקטורת Daemon

לפני הגדרת ה-Hooks האישיים בכל תוכנה, חשוב להבין את העקרונות ההנדסיים של RightSub:

### ⚙️ מודל שני השלבים
1. **שלב א': תיקון רטרואקטיבי חד-פעמי של כל הספרייה (One-Off Batch Fix)**  
   הריצו את RightSub פעם אחת על כל תיקיית ספריית המדיה הקיימת:
   ```bash
   # ב-Windows:
   rightsub auto "C:\Media\TV Shows"

   # ב-macOS / Linux:
   rightsub auto /Volumes/Media/TV_Shows
   ```
   RightSub סורק רקורסיבית את כל התיקיות, ממיר קידודים מיושנים (CP1255/Windows-1255) ל-UTF-8, מחיל תווי RLM לתיקון כיווניות סימני פיסוק בפלקס, מנקה פרסומות ו-SDH, ומייצר קובצי `.he.srt` תקניים מבלי לפגוע בקובצי ההורדה המקוריים.
2. **שלב ב': אוטומציה שוטפת ללא צורך בהתערבות (Event-Driven Hooks)**  
   מכאן ואילך, **אין צורך** בסורק רקע רציף ומכביד. מגדירים את מנהלי ההורדות (qBittorrent, Sonarr, Radarr, Bazarr) להפעיל את RightSub **אך ורק בשנייה שבה קובץ מדיה חדש מסיים לרדת**.

### 🏛️ מדוע ארכיטקטורת Hooks עדיפה על פני דמון רקע רציף (24/7 Daemon)?

משתמשים תוהים לעיתים קרובות: *"מדוע RightSub לא פועלת כ-Daemon רציף שסורק תיקיות כל הזמן?"*

במערכי מדיה והורדות ביתיים, דמון סורק תיקיות רציף הוא **Anti-Pattern ארכיטקטוני**:
1. **סכנת Race Conditions ונעילת קבצים חלקיים**: כאשר קליינט טורנט מוריד קובץ וידאו של 15GB או מחלץ ארכיון, הכתיבה לדיסק נמשכת דקות ואף שעות. דמון סורק מזהה את הקובץ מיד עם יצירתו, ומנסה לקרוא או לנעול קובץ חלקי שנמצא באמצע כתיבה — מה שגורם לקריסות ולקובצי כתוביות פגומים.
2. **אפס צריכת משאבים בשגרה (Zero Idle Resource Consumption)**: דמון רקע מחזיק סביבת Python פעילה בזיכרון ה-RAM באופן רציף (40–80 MB) ומעיר ליבות מעבד לצורך בדיקות תקופתיות. ארכיטקטורת ה-Hooks צורכת **0% מעבד ו-0 MB זיכרון בשגרה** — RightSub מתעורר לשבריר שנייה רק כשקובץ הושלם, מבצע את העיבוד ונסגר מיידית.
3. **פעולה אטומית ובטוחה (Atomic Execution)**: מנהלי ההורדות יודעים בוודאות מתמטית מתי הקובץ סיים לרדת, עבר בהצלחה בדיקת Hash ונסגר לכתיבה. הפעלת הסקריפט באותו רגע מבטיחה אפס תקלות.

---

## 1. qBittorrent (הפעלה בסיום הורדה ושמירה על שיתוף)

qBittorrent יכולה להפעיל את RightSub בדיוק בשנייה שבה סרט או פרק מסיים לרדת.

### היתרון המהותי: שמירה על שיתוף טורנטים (Seed-Safe)
בדרך כלל, שינוי של קובץ כתוביות שהורד (כגון שינוי שם מ-`Movie.srt` ל-`Movie.he.srt` או תיקון תוכן הטקסט) משנה את ה-Hash של הקובץ וגורם ל-qBittorrent לזרוק שגיאת שיתוף (`I/O Error` / בדיקת תקינות נכשלת).  
מנגנון ה-**Seed-Safe** המובנה של RightSub מונע זאת לחלוטין: הוא **משכפל** את הכתובית לעותק חדש בשם התקני עבור פלקס (`Movie.he.srt`) ומבצע עליו את התיקון, בעוד קובץ המקור נשאר **100% זהה ברמת הביט (Bit-for-Bit)**. שיתוף הטורנט (Seeding) ממשיך לרוץ ברקע ללא שום הפרעה.

### כיצד להגדיר:
1. פתחו את qBittorrent.
2. היכנסו ל: **כלים** -> **אפשרויות** (או `Preferences` ב-macOS).
3. בחרו בלשונית **הורדות** (Downloads) בסרגל הצדדי.
4. גללו לתחתית העמוד וסמנו ב-V:  
   ☑ **"הפעל תוכנית חיצונית בסיום ההורדה"** (Run external program on torrent completion).
5. הדביקו את הפקודה המתאימה למערכת ההפעלה שלכם:

#### ב-Windows (ב-CMD או PowerShell):
```cmd
rightsub auto "%F"
```
*(במידה ו-`rightsub` אינה מוגדרת ב-PATH הכללי, ציינו את הנתיב המלא: `python "C:\path\to\RightSub\rightsub.py" auto "%F"`)*

#### ב-macOS / Linux (ב-Terminal):
```bash
/usr/local/bin/rightsub auto "%F"
```
*(או `~/.local/bin/rightsub auto "%F"`)*

> **הערה על משתנה `%F`**: qBittorrent מחליפה אוטומטית את `%F` בנתיב המלא של הקובץ או התיקייה שסיימו לרדת.

---

## 2. Sonarr ו-Radarr (אינטגרציית Webhook או סקריפט ייבוא)

Sonarr ו-Radarr מאפשרות להפעיל עיבוד חיצוני מיד לאחר שסדרה או סרט עברו סיווג, שינוי שם והעברה לספריית המדיה הסופית (`On Download`, `On Upgrade` ו-`On Movie Imported`).

RightSub מציעה שתי שיטות חיבור:
- **שיטה א' (מומלצת ל-Docker, Unraid, TrueNAS, Synology)**: שרת Webhook עצמאי ללא צורך בהתקנת פייתון או סקריפטים בתוך הקונטיינר.
- **שיטה ב' (למערכות Bare-Metal)**: סקריפט מקומי (Custom Script).

---

### שיטה א' (מומלצת): שרת Webhook לקונטיינרים (`rightsub serve`)

כאשר Sonarr ו-Radarr רצות בקונטיינרים מבודדים, אין אפשרות להריץ סקריפטים של המחשב המארח. שרת ה-Webhook המובנה של RightSub פותר זאת בחיבור HTTP ישיר:

#### שלב 1: הפעלת שרת ה-Webhook של RightSub
```bash
# הרצה מקומית או בתוך Docker:
rightsub serve --port 8775 --path-map "/data/media:/media"

# או פריסה באמצעות docker-compose.yml:
docker compose up -d
```
*(לפרטים נוספים על תרגום נתיבים ראו [פרק תרגום נתיבים PATH_MAP](#-תרגום-נתיבים-חוצה-קונטיינרים-path_map))*

#### שלב 2: הגדרה ב-Sonarr / Radarr
1. היכנסו לממשק ה-Web של **Sonarr** או **Radarr**.
2. נווטו ל: **Settings** -> **Connect**.
3. לחצו על כפתור ה-**`+`** ובחרו באפשרות **Webhook**.
4. מלאו את השדות:
   - **Name**: `RightSub Subtitle Master`
   - **Notification Triggers**: סמנו ב-V את ☑ **On Download**, ☑ **On Upgrade**, וב-Radarr גם ☑ **On Movie Imported**.
   - **URL**: 
     - אם RightSub רץ באותה רשת Docker: `http://rightsub:8775/webhook/sonarr` (או `/webhook/radarr`).
     - אם RightSub רץ במארח/שרת נפרד: `http://IP-OF-SERVER:8775/webhook/sonarr`.
   - **Method**: `POST`
5. לחצו על **Test** — שרת ה-RightSub יחזיר תשובת `200 OK` מיידית ויאשר את החיבור.
6. לחצו על **Save**.

---

### שיטה ב': סקריפט מקומי (Custom Script למשתמשי Bare-Metal)

למשתמשים המתקינים ישירות על מערכת ההפעלה המארחת:

#### שלב א': יצירת קובץ ה-Hook המתווך

##### ב-Windows: יצירת הקובץ `C:\Scripts\rightsub_arr_hook.bat`
```cmd
@echo off
setlocal

:: Sonarr מעבירה את sonarr_episodefile_path; Radarr מעבירה את radarr_moviefile_path
set "TARGET_PATH="
if defined sonarr_episodefile_path set "TARGET_PATH=%sonarr_episodefile_path%"
if defined radarr_moviefile_path set "TARGET_PATH=%radarr_moviefile_path%"

if defined TARGET_PATH (
    rightsub auto "%TARGET_PATH%"
)
```

##### ב-macOS / Linux: יצירת הקובץ `/usr/local/bin/rightsub_arr_hook.sh`
```bash
#!/usr/bin/env bash
TARGET_PATH="${sonarr_episodefile_path:-$radarr_moviefile_path}"

if [ -n "$TARGET_PATH" ] && [ -f "$TARGET_PATH" ]; then
    /usr/local/bin/rightsub auto "$TARGET_PATH"
fi
```
*(יש לתת הרשאת הרצה: `chmod +x /usr/local/bin/rightsub_arr_hook.sh`)*

#### שלב ב': הגדרה בממשק של Sonarr / Radarr
1. היכנסו ל: **Settings** -> **Connect**.
2. לחצו על כפתור ה-**`+`** ובחרו באפשרות **Custom Script**.
3. מלאו את השדות:
   - **Name**: `RightSub Auto-Master`
   - **Notification Triggers**: סמנו ב-V את ☑ **On Download** ואת ☑ **On Upgrade**.
   - **Path**: הגדירו את הנתיב לקובץ שיצרתם (`C:\Scripts\rightsub_arr_hook.bat` או `/usr/local/bin/rightsub_arr_hook.sh`).
4. לחצו על **Test** ולאחר מכן על **Save**.

---

## 3. Bazarr (אינטגרציית Webhook או Post-Processing)

Bazarr מורידה כתוביות ממעל 30 מאגרים ברשת. אולם כתוביות אלו סובלות באופן קבוע מבעיות חמורות:
- ❌ סימני פיסוק הפוכים ב-Plex וב-Apple TV (`?`, `!`, `...`, נקודות ומקפים).
- ❌ קידודי עברית מיושנים (Windows-1255 / ISO-8859-8) המופיעים כג'יבריש מוחלט.
- ❌ שורות פרסומת וקרדיטים מטרידים ("סונכרן ע\"י Torec", "SubCenter", כתובות טלגרם).

RightSub פותרת את הבעיה הזו בדיוק בשנייה שהכתובית נוחתת על הדיסק:
- **שיטה א' (מומלצת): Webhook ישיר מ-Bazarr לשרת RightSub** (עובד מעולה בקונטיינרים וב-NAS).
- **שיטה ב': Post-Processing פנימי** (לסביבות שאינן בקונטיינר).

---

### שיטה א' (מומלצת): חיבור Webhook מובנה מ-Bazarr ל-RightSub

זוהי הדרך האלגנטית, המהירה והיציבה ביותר, שאינה דורשת התקנת סקריפטים בתוך קונטיינר ה-Bazarr:

#### שלב 1: ודאו ששרת ה-RightSub פעיל
```bash
# הרצת השרת בפורט 8775 (ברירת מחדל):
rightsub serve --port 8775 --path-map "/data/media:/media"
```

#### שלב 2: הגדרה בממשק Bazarr
1. פתחו את ממשק ה-Web של Bazarr (`http://localhost:6767` או ה-IP של השרת שלכם).
2. נווטו בסרגל העליון/צדדי ל: **Settings** -> **Notifications**.
3. לחצו על כפתור ה-**`+`** (הוספת התראה חדשה) ובחרו ב-**Webhook**.
4. הגדירו את הפרמטרים הבאים:
   - **Name**: `RightSub BiDi & Hebrew Master`
   - **URL**: 
     - ברשת Docker פנימית: `http://rightsub:8775/webhook/bazarr`
     - או עם כתובת שרת המדיה: `http://192.168.1.X:8775/webhook/bazarr`
   - **HTTP Method**: `POST`
   - **Notification Types**:
     - סמנו ב-V אך ורק את: ☑ **On Subtitles Download** (או `On subtitles download`).
5. לחצו על כפתור **Test**:
   - שרת ה-RightSub ירשום ביומן: `[Webhook] Received Bazarr test ping.` ויחזיר `200 OK`.
6. לחצו על **Save**.

#### מה קורה עכשיו בכל פעם ש-Bazarr מורידה כתובית?
1. Bazarr שולחת קריאת `POST /webhook/bazarr` עם נתיב הכתובית ושפתה (`language: "he"`).
2. שרת ה-RightSub:
   - מוודא שהשפה היא עברית (מדלג אוטומטית ובשקט על הורדות בשפות אחרות כמו אנגלית או צרפתית).
   - מתרגם את נתיב הקובץ דרך `PATH_MAP` אם Bazarr רואה נתיב שונה מהשרת.
   - מפעיל את מנוע ה-**SubRefine**:
     - הופך סימני פיסוק והוראות כיווניות בעזרת תווי RLM נסתרים.
     - מזהה וממיר קידוד מ-Windows-1255 ל-UTF-8 נקי.
     - מנקה שורות פרסומת ורעשי שמע (SDH).
   - מעדכן את חותמת הזמן של הקובץ (`os.utime`) כך ש-Plex ו-Infuse מזהים מיד את העדכון ללא צורך בסריקה מחדש.
3. כל התהליך מתבצע תוך **0.05 עד 0.1 שניות בלבד**!

---

### שיטה ב': Custom Post-Processing (למשתמשי Bare-Metal)

למשתמשים שאינם משתמשים בקונטיינרים ומריצים את Bazarr ישירות על ה-Host:

1. היכנסו לממשק ה-Web של Bazarr (`http://localhost:6767`).
2. נווטו ל: **Settings** -> **Subtitles** -> **Post-processing**.
3. תחת **Custom Post-Processing**:
   - סמנו ב-V את ☑ **Enable custom post-processing**.
   - בשורת ה-**Command** הזינו:

#### ב-Windows:
```cmd
rightsub auto "{{subtitles_path}}"
```

#### ב-macOS / Linux:
```bash
rightsub auto "{{subtitles_path}}"
```
4. לחצו על **Save** בפינה השמאלית העליונה לשמירה.

---

### 🌐 תרגום נתיבים חוצה-קונטיינרים (PATH_MAP)

בסביבות קונטיינרים (כגון Docker Compose, Unraid, TrueNAS SCALE), שרתי ה-`*arr` וה-Bazarr עשויים למפות את תיקיית המדיה לנתיב שונה מזה של RightSub.
לדוגמה:
- Bazarr רואה את הכתובית ב: `/data/media/tv/show.he.srt`
- RightSub ממפה את כונן המדיה ל: `/media/tv/show.he.srt`

הגדירו את המשתנה `PATH_MAP` בהרצת השרת:
```bash
# תחביר: FROM_PREFIX:TO_PREFIX
rightsub serve --path-map "/data/media:/media"

# או בסביבת Docker / Compose:
environment:
  - PATH_MAP=/data/media:/media
```
RightSub יחליף אוטומטית את קידומת הנתיב עבור כל Webhook שמגיע מ-Bazarr או מ-Sonarr/Radarr!

---

## 4. Transmission (סקריפט סיום ב-macOS/Linux)

עבור משתמשי Transmission daemon או קליינט ב-Mac/Linux/NAS:

### שלב א': יצירת הסקריפט `/usr/local/bin/transmission_rightsub.sh`
```bash
#!/usr/bin/env bash
# Transmission מעבירה את משתני הסביבה $TR_TORRENT_DIR ו-$TR_TORRENT_NAME
TARGET_DIR="${TR_TORRENT_DIR}/${TR_TORRENT_NAME}"

if [ -e "$TARGET_DIR" ]; then
    /usr/local/bin/rightsub auto "$TARGET_DIR"
fi
```
*(הענקת הרשאות: `chmod +x /usr/local/bin/transmission_rightsub.sh`)*

### שלב ב': הפעלה בקובץ `settings.json` של Transmission:
```json
"script-torrent-done-enabled": true,
"script-torrent-done-filename": "/usr/local/bin/transmission_rightsub.sh"
```

---

## 5. Tautulli / Plex (בדיקה עם קליטת מדיה חדשה)

עבור משתמשי Tautulli המנטרים את שרת ה-Plex שלהם ומעוניינים לוודא תקינות כתוביות מיידית עם הוספת תוכן חדש:

### כיצד להגדיר:
1. ב-Tautulli, גשו ל: **Settings** -> **Notification Agents**.
2. לחצו על **Add a Notification Agent** -> בחרו **Script**.
3. ב-**Script Folder** בחרו את התיקייה שבה שמור הסקריפט.
4. ב-**Script File** בחרו את `rightsub_arr_hook.bat` (ב-Windows) או `rightsub_arr_hook.sh` (ב-macOS/Linux).
5. בלשונית **Triggers**, סמנו ב-V את ☑ **Recently Added**.
6. בלשונית **Arguments**, תחת **Recently Added**, הזינו:
   ```text
   <file>
   ```
7. שמרו את הסוכן. RightSub תוודא את תקינות הכתובית לפני שמישהו בבית ילחץ על Play.

---

## 6. ניטור תיקיות מקומי עצמאי (ללא תוכנות Arr / העתקה ידנית)

עבור משתמשים ש**אינם** נעזרים בתוכנות הורדה אוטומטיות (כמו qBittorrent, Sonarr או Radarr) אלא מעתיקים או גוררים קבצים ידנית לתיקיית יעד, ניתן להגדיר מנגנון ניטור מקומי קל-משקל ברמת מערכת ההפעלה הכולל **מנגנון הגנה מפני קבצים חלקיים (Write-Settle)**:

### ב-macOS: שימוש ב-Folder Action עם לולאת בדיקת יציבות
צרו Automator Folder Action המשויך לתיקיית ההורדות שלכם (למשל `~/Downloads` או `/Volumes/Media/Incoming`) עם פעולת **Run Shell Script**:

```bash
#!/usr/bin/env bash
for f in "$@"; do
    # סינון קובצי וידאו וכתוביות בלבד
    case "$f" in
        *.mkv|*.mp4|*.avi|*.srt) ;;
        *) continue ;;
    esac

    # בדיקת יציבות: מוודא שהקובץ סיים להיכתב ואינו חלקי
    PREV_SIZE=-1
    while true; do
        CURR_SIZE=$(stat -f%z "$f" 2>/dev/null || echo 0)
        if [ "$CURR_SIZE" -eq "$PREV_SIZE" ] && [ "$CURR_SIZE" -gt 0 ]; then
            break
        fi
        PREV_SIZE="$CURR_SIZE"
        sleep 2
    done

    /usr/local/bin/rightsub auto "$f"
done
```

### ב-Windows: סקריפט ניטור ב-PowerShell (`rightsub_watcher.ps1`)
שמרו את הסקריפט הבא והפעילו אותו בעליית המחשב (או דרך ה-Windows Task Scheduler):

```powershell
param (
    [string]$WatchFolder = "C:\Users\$env:USERNAME\Downloads"
)

Write-Host "[*] RightSub Folder Watcher פעיל על התיקייה: $WatchFolder"
$watcher = New-Object System.IO.FileSystemWatcher $WatchFolder, "*.*" -Property @{
    IncludeSubdirectories = $false
    NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite
}

Register-ObjectEvent $watcher "Created" -Action {
    $path = $Event.SourceEventArgs.FullPath
    $ext = [System.IO.Path]::GetExtension($path).ToLower()
    if ($ext -notin @(".mkv", ".mp4", ".avi", ".srt")) { return }

    # המתנה עד שהקובץ משתחרר לחלוטין מנעילת כתיבה (ההעתקה הסתיימה)
    while ($true) {
        try {
            $stream = [System.IO.File]::Open($path, 'Open', 'Read', 'None')
            $stream.Close()
            break
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    Write-Host "[+] מעבד קובץ שהושלם: $path"
    rightsub auto "$path"
}

# השארת הסקריפט פעיל ברקע
while ($true) { Start-Sleep -Seconds 60 }
```

---

## 7. 💡 אימות ובדיקת פעולה (Troubleshooting)

כדי לוודא שהתהליך האוטומטי מתבצע בצורה תקינה:
1. הריצו פקודת סימולציה (Dry Run) על קובץ לדוגמה:
   ```bash
   rightsub auto "/path/to/Sample.mkv" --dry-run
   ```
2. פתחו את דוח האנליטיקס ההיסטורי ב-`docs/analytics/TRAFFIC_REPORT.md` כדי לראות פעילות תיעוד שוטפת של המערכת.

</div>
