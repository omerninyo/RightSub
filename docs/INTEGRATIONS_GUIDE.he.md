<div dir="rtl">

# 🔄 מדריך אינטגרציות ואוטומציה לשרתי מדיה (Home Media Integrations)

> **סקירה כללית**: הפעלת RightSub באופן אוטונומי מלא בכל מערך ההורדות והמדיה שלכם בתצורת "הגדר ושכח" (Set-and-Forget). המדריך כולל הגדרות מוכנות להעתקה והדבקה עבור שרתי מדיה ומנהלי הורדות.

המדריך מכסה הגדרות מלאות ומאומתות עבור **Windows** ועבור **macOS/Linux**:
1. [qBittorrent (הפעלה אוטומטית בסיום הורדה ושמירה על טורנטים)](#1-qbittorrent-הפעלה-בסיום-הורדה-ושמירה-על-שיתוף)
2. [Sonarr ו-Radarr (סקריפטי ייבוא Connect)](#2-sonarr-ו-radarr-סקריפטי-חיבור-connect)
3. [Bazarr (הרצה כ-Post-Processing)](#3-bazarr-עיבוד-והשבחה-לאחר-הורדה)
4. [Transmission (סקריפט סיום הורדה)](#4-transmission-סקריפט-סיום-ב-macoslinux)
5. [Tautulli / Plex (בדיקת מדיה שנוספה לאחרונה)](#5-tautulli--plex-בדיקה-עם-קליטת-מדיה-חדשה)

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

## 2. Sonarr ו-Radarr (סקריפטי חיבור Connect)

Sonarr ו-Radarr מאפשרות להריץ סקריפטים חיצוניים מיד לאחר שסדרה או סרט עברו סיווג, שינוי שם והעברה לספריית המדיה הסופית (`On Download` ו-`On Upgrade`).

### מה קורה באופן אוטומטי?
RightSub סורקת את קובץ המדיה החדש:
1. מחלצת כתוביות מובנות (באנגלית או עברית) מתוך קובץ ה-MKV/MP4.
2. אם קיימת כתובית בעברית — מתקנת אותה מיידית לפלקס (הזרקת RLM ל-BiDi, המרת קידוד ל-UTF-8 וניקוי פרסומות ורעשי שמע).
3. אם אין כתובית בעברית — מכינה מראש מנות תרגום באנגלית מוכנות לתרגום AI.

### שלב א': יצירת קובץ ה-Hook המתווך

#### ב-Windows: יצירת הקובץ `C:\Scripts\rightsub_arr_hook.bat`
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

#### ב-macOS / Linux: יצירת הקובץ `/usr/local/bin/rightsub_arr_hook.sh`
```bash
#!/usr/bin/env bash
TARGET_PATH="${sonarr_episodefile_path:-$radarr_moviefile_path}"

if [ -n "$TARGET_PATH" ] && [ -f "$TARGET_PATH" ]; then
    /usr/local/bin/rightsub auto "$TARGET_PATH"
fi
```
*(יש לתת הרשאת הרצה: `chmod +x /usr/local/bin/rightsub_arr_hook.sh`)*

### שלב ב': הגדרה בממשק של Sonarr / Radarr
1. היכנסו ל: **Settings** -> **Connect**.
2. לחצו על כפתור ה-**`+`** ובחרו באפשרות **Custom Script**.
3. מלאו את השדות:
   - **Name**: `RightSub Auto-Master`
   - **Notification Triggers**: סמנו ב-V את ☑ **On Download** ואת ☑ **On Upgrade**.
   - **Path**: הגדירו את הנתיב לקובץ שיצרתם (`C:\Scripts\rightsub_arr_hook.bat` או `/usr/local/bin/rightsub_arr_hook.sh`).
4. לחצו על **Test** ולאחר מכן על **Save**.

---

## 3. Bazarr (עיבוד והשבחה לאחר הורדה)

Bazarr מאתרת כתוביות קהילתיות ברשת ומורידה אותן, אך ברוב המקרים כתוביות אלו כוללות היפוכי פיסוק, קידודי ג'יבריש ופרסומות. חיבור RightSub כ-Post-Processing משלים את הפעולה והופך כל קובץ ש-Bazarr מורידה למושלם עבור פלקס.

### כיצד להגדיר:
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

## 💡 אימות ובדיקת פעולה (Troubleshooting)

כדי לוודא שהתהליך האוטומטי מתבצע בצורה תקינה:
1. הריצו פקודת סימולציה (Dry Run) על קובץ לדוגמה:
   ```bash
   rightsub auto "/path/to/Sample.mkv" --dry-run
   ```
2. פתחו את דוח האנליטיקס ההיסטורי ב-`docs/analytics/TRAFFIC_REPORT.md` כדי לראות פעילות תיעוד שוטפת של המערכת.

</div>
