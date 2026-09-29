<div dir="rtl">

# 🔮 מפרט ארכיטקטוני לפיתוח עתידי: שרת Webhook וקונטיינר Docker לאינטגרציית Sonarr, Radarr ו-Bazarr

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="Docker-Webhook-Server-Specification"><b>English</b></a>
</p>

מסמך זה מגדיר את עקרונות התכנון, הארכיטקטורה, חוזי ה-API ומודל הפריסה עבור **שרת ה-Webhook המובנה וקונטיינר ה-Docker הרשמי של RightSub**.  
מטרת הרכיב היא לאפשר אינטגרציה חלקה (Zero-Kludge Plug-and-Play) מול שרתי מדיה ביתיים (Unraid, TrueNAS SCALE, Synology DSM, Docker Compose) ומול מנהלי הורדות (`*arr` Stack ו-Bazarr) ללא צורך בהתקנת סביבות פייתון על המארח וללא כתיבת סקריפטים ידניים.

---

## 1. רקע והגדרת הבעיה ההנדסית (Problem Statement)

1. **בידוד קונטיינרים בשרתי Homelab ו-NAS:**
   - רוב שרתי המדיה מריצים את Sonarr, Radarr ו-Bazarr בתוך קונטיינרים מבודדים של Docker.
   - מערכות הפעלה מודרניות ל-NAS (כגון Unraid, TrueNAS SCALE ו-Synology DSM) אינן מיועדות להתקנת ספריות פייתון או כלי מערכת ישירות על מערכת ההפעלה של ה-Host.
2. **הכשל בהפעלת סקריפטים מקומיים (Custom Scripts) מתוך קונטיינר:**
   - כאשר משתמש מנסה להגדיר פקודת Post-Processing בתוך Bazarr או Sonarr המריצה `rightsub auto`, הפקודה נכשלת מיד עם שגיאת `command not found`, כיוון שהקונטיינר של Bazarr אינו מכיל את RightSub.
3. **הפתרונות הקיימים בקהילה כיום ("סקריפטים עקומים"):**
   - משתמשים נאלצים להרים שרתי Web מאולתרים ב-Python/Flask או סקריפטי cron המופעלים ידנית מול ה-API של Bazarr כדי לנסות לתקן את פיסוק ה-RTL בכתוביות.
4. **ההזדמנות הטכנית ב-Webhooks של משפחת `*arr` ו-Bazarr:**
   - ל-Sonarr, Radarr ו-Bazarr יש מנועי התראות מובנים (Webhooks) היודעים לשלוח בקשת HTTP POST עם מטען JSON מובנה בשנייה שבה קובץ מדיה או כתובית מגיעים לדיסק.

---

## 2. מטרות ועקרונות יסוד

1. **אפס תלויות שרת כבדות (Zero Heavy Frameworks):**
   - שרת ה-Webhook יוטמע ישירות בליבת RightSub ויופעל באמצעות הפקודה `rightsub serve --port 8775`.
   - יישום קל-משקל המבוסס על ספריות הפייתון המובנות (`http.server` / `asyncio`) או מיקרו-פריימוורק מהיר במיוחד, הצורך פחות מ-15 MB זיכרון RAM במנוחה.
2. **תמיכה מקורית בפורמטי ה-JSON של Sonarr, Radarr ו-Bazarr:**
   - פענוח אוטומטי של המטען ללא צורך בהגדרת פרמטרים מורכבים מצד המשתמש.
3. **מיפוי נתיבים אוטונומי (Path Mapping):**
   - גישור על פער הנתיבים הנוצר כאשר קונטיינר Sonarr רואה את הקובץ ב-`/data/media/tv` בעוד קונטיינר RightSub רואה אותו ב-`/tv`.
4. **שימור מוחלט של שיתוף טורנטים (Seed-Safe Guarantee):**
   - השרת לעולם אינו משנה קובצי כתוביות מקוריים השייכים לטורנטים פעילים. תמיד ייווצר עותק צמוד ממוסטר (`<stem>.he.srt`).
5. **עדכון מטא-דאטה מואץ ל-Plex ו-Infuse:**
   - ביצוע `os.utime()` אוטומטי המבטיח שהנגן יזהה את הכתובית החדשה מיד ללא צורך בסריקה ידנית.

---

## 3. ארכיטקטורת חוזה ה-API (Endpoint Specifications)

שרת ה-Webhook יאזין לפורט ברירת מחדל `8775` (הניתן להגדרה דרך משתנה סביבה `RIGHTSUB_PORT` או דגל `--port`):

### א. `POST /webhook/sonarr` (התראות Sonarr)
- **אירועים נתמכים:** `Download`, `Upgrade`, `Rename`.
- **מבנה מטען טיפוסי:**
  ```json
  {
    "eventType": "Download",
    "series": {
      "title": "Boston Legal",
      "path": "/data/media/tv/Boston Legal"
    },
    "episodeFile": {
      "relativePath": "Season 01/Boston Legal - S01E01.mkv",
      "path": "/data/media/tv/Boston Legal/Season 01/Boston Legal - S01E01.mkv"
    }
  }
  ```
- **לוגיקת עיבוד:**
  1. המרת הנתיב לפי טבלת ה-`PATH_MAP`.
  2. סריקת תיקיית הפרק לאיתור קובצי כתוביות צמודים (`.srt`), או חילוץ רצועת כתובית עברית מוטמעת מתוך הווידאו.
  3. הפעלת מנוע `SubRefine` (תיקון פיסוק BiDi RLM, ניקוי SDH והמרת קידודי CP1255).
  4. החזרת סטטוס `200 OK` עם פירוט הפעולות שבוצעו.

### ב. `POST /webhook/radarr` (התראות Radarr)
- **אירועים נתמכים:** `Download`, `MovieFileImported`.
- **מבנה מטען טיפוסי:**
  ```json
  {
    "eventType": "Download",
    "movie": {
      "title": "Gladiator",
      "folderPath": "/data/media/movies/Gladiator (2000)"
    },
    "movieFile": {
      "relativePath": "Gladiator (2000).mkv",
      "path": "/data/media/movies/Gladiator (2000)/Gladiator (2000).mkv"
    }
  }
  ```
- **לוגיקת עיבוד:** זהה למסלול Sonarr, מותאמת למבנה סרטים.

### ג. `POST /webhook/bazarr` (התראות Bazarr)
- **אירועים נתמכים:** `Subtitle Downloaded`.
- **מבנה מטען טיפוסי (Bazarr Webhook Notification):**
  ```json
  {
    "event": "download",
    "subtitle": {
      "path": "/data/media/tv/Boston Legal/Season 01/Boston Legal - S01E01.he.srt",
      "language": "he"
    }
  }
  ```
- **לוגיקת עיבוד:**
  - בדיקה האם שפת הכתובית היא עברית (`he` / `heb`).
  - אם השפה עברית: ביצוע מאסטרינג מיידי לקובץ הכתוביות (RLM, קידוד, ניקוי רעשים).
  - הפעולה אורכת כ-0.05 עד 0.2 שניות.

### ד. `POST /webhook/generic` או `POST /process`
- נקודת קצה כללית לקריאות יזומות מסקריפטים חיצוניים:
  ```json
  {
    "path": "/media/tv/show.srt",
    "action": "refine"
  }
  ```

### ה. `GET /health`
- מחזיר בדיקת תקינות, גרסה, מונה קבצים שעובדו וזמן פעילות (Uptime):
  ```json
  {
    "status": "healthy",
    "version": "1.4.0",
    "uptime_seconds": 86400,
    "processed_count": 142
  }
  ```

---

## 4. מנגנון מיפוי נתיבים (Container Path Mapping)

בסביבות Docker, כל קונטיינר עשוי למפות את תיקיית האחסון בנתיב שונה.  
RightSub תתמוך במשתנה סביבה גמיש: `PATH_MAP`.

**פורמט התחביר:** `MAPPING=FROM_PREFIX:TO_PREFIX[,FROM_2:TO_2]`  
**דוגמה:**
```bash
PATH_MAP="/data/media:/media"
```
אם מתקבל נתיב מ-Sonarr:
`/data/media/tv/Boston Legal/S01E01.mkv`  
השרת של RightSub ימיר אותו אוטומטית ל:
`/media/tv/Boston Legal/S01E01.mkv`

---

## 5. הגדרת פריסה: Docker Compose ו-Unraid

### דוגמת `docker-compose.yml` מלאה:
```yaml
version: "3.8"

services:
  rightsub:
    image: ghcr.io/omerninyo/rightsub:latest
    container_name: rightsub
    restart: unless-stopped
    ports:
      - "8775:8775"
    environment:
      - RIGHTSUB_PORT=8775
      - PATH_MAP=/data/media:/media
      - PUID=1000
      - PGID=1000
      - TZ=Asia/Jerusalem
    volumes:
      - /mnt/storage/media:/media
      - /mnt/storage/appdata/rightsub:/config
```

### הגדרה ב-Sonarr / Radarr:
1. נווט אל: `Settings` -> `Connect` -> לחץ על `+` ובחר ב-`Webhook`.
2. **Name:** `RightSub BiDi Master`
3. **URL:** `http://rightsub:8775/webhook/sonarr` (או כתובת ה-IP של שרת ה-Docker).
4. **Method:** `POST`
5. **Triggers:** סמן את `On Download` ו-`On Upgrade`.
6. לחץ על **Test** ו-**Save**.

### הגדרה ב-Bazarr:
1. נווט אל: `Settings` -> `Notifications` -> בחר ב-`Webhook`.
2. **URL:** `http://rightsub:8775/webhook/bazarr`
3. **Notification Types:** סמן את `On Subtitles Download`.

---

## 6. תוכנית מימוש עבור גרסה 1.4.0

1. **שלב 1 (Core Webhook Daemon):**
   - כתיבת מודול `src/daemon/webhook_server.py` המבוסס על `http.server` ללא תלויות צד שלישי כבדות.
   - מימוש המפענחים הייעודיים ל-Sonarr, Radarr ו-Bazarr.
2. **שלב 2 (Path Mapping & Multi-threading):**
   - מנגנון תרגום נתיבים גלובלי.
   - טיפול בבקשות בתור אסינכרוני (Thread pool / Queue) למניעת חסימת ה-HTTP response בעת עיבוד קבצים כבדים.
3. **שלב 3 (Docker Packaging & GHCR Pipeline):**
   - כתיבת `Dockerfile` רזה (מבוסס `python:3.11-slim`).
   - הגדרת GitHub Action לבנייה ודחיפה אוטומטית של תגיות `latest` ו-`v1.4.0` ל-`ghcr.io`.
   - יצירת תבנית XML רשמית עבור Unraid Community Applications.

</div>
