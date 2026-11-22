<div dir="rtl">

# 🐳 מפרט ארכיטקטוני: שרת Webhook וקונטיינר Docker לאינטגרציית Sonarr, Radarr ו-Bazarr (`rightsub serve`)

> **סטטוס:** ✅ **שוחרר בייצור (`v1.4.0`–`v1.5.1`)** — מומש ב-[`scripts/21_webhook_server.py`](https://github.com/omerninyo/RightSub/blob/main/scripts/21_webhook_server.py), ב-[`Dockerfile`](https://github.com/omerninyo/RightSub/blob/main/Dockerfile) וב-[`docker-compose.yml`](https://github.com/omerninyo/RightSub/blob/main/docker-compose.yml). מאומת על ידי [`tests/test_webhook_server.py`](https://github.com/omerninyo/RightSub/blob/main/tests/test_webhook_server.py).

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="Docker-Webhook-Server-Specification"><b>English</b></a>
</p>

מסמך זה מגדיר את עקרונות התכנון, הארכיטקטורה, חוזי ה-API, הקשחת האבטחה ומודל הפריסה עבור **שרת ה-Webhook המובנה וקונטיינר ה-Docker הרשמי של RightSub** (`rightsub serve`).  
השרת מאפשר אינטגרציה חלקה (Zero-Kludge Plug-and-Play) מול שרתי מדיה ביתיים (Unraid, TrueNAS SCALE, Synology DSM, Docker Compose) ומול מנהלי הורדות (`*arr` Stack ו-Bazarr) ללא צורך בהתקנת סביבות פייתון על המארח וללא כתיבת סקריפטים ידניים.

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
   - יישום קל-משקל המבוסס בלעדית על ספריות הליבה של Python (`http.server.ThreadingHTTPServer`) ללא תלויות חיצוניות, הצורך פחות מ-15 MB זיכרון RAM במנוחה.
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
- מחזיר בדיקת תקינות, גרסה, נקודות קצה ומדדי עיבוד:
  ```json
  {
    "status": "healthy",
    "service": "RightSub Webhook Daemon",
    "version": "1.5.1",
    "uptime_seconds": 86400.0,
    "metrics": {
      "events_count": 142,
      "processed_count": 142,
      "errors_count": 0
    },
    "endpoints": ["/ui", "/health", "/webhook/sonarr", "/webhook/radarr", "/webhook/bazarr", "/webhook/generic"]
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

## 5. הגדרת פריסה: Docker Compose וקונטיינר

### דוגמת `docker-compose.yml` מלאה:
```yaml
services:
  rightsub:
    image: ghcr.io/omerninyo/rightsub:latest
    container_name: rightsub
    restart: unless-stopped
    ports:
      - "8775:8775"
    environment:
      - RIGHTSUB_PORT=8775
      - RIGHTSUB_CONFIG_DIR=/config
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

## 6. פרטי המימוש בייצור (`v1.4.0`–`v1.5.1`)

1. **ליבת שרת ה-Webhook והממשק המקומי (`/ui`):**
   - ממומשת במודול `scripts/21_webhook_server.py` (`ThreadingHTTPServer`) ללא תלויות צד שלישי, עם מפענחי Sonarr, Radarr ו-Bazarr והגשה מובנית של סדנת הדפדפן ב-`/ui`.
2. **נעילות, הגנת Seed-Safe והקשחת אבטחה:**
   - נעילות ברמת קובץ (`_get_file_lock`) וכתיבה אטומית מונעות התנגשויות מקביליות; מצב Seed-Safe מופעל כברירת מחדל.
   - גרסה `1.5.1` מוסיפה אימות `--api-key`, הגבלת תיקיות `--allowed-roots`, אכיפת `Content-Type: application/json`, והאזנה מאובטחת על `127.0.0.1` בשירותי OS.
3. **אריזת Docker (`Dockerfile`):**
   - תמונת `Dockerfile` נקייה ללא משתמש root המבוססת על `python:3.12-slim` עם `RIGHTSUB_CONFIG_DIR=/config`.

</div>
