<div dir="rtl">

# 🗺️ מפת דרכים ומעקב אבני-דרך — RightSub (Product Roadmap)

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="ROADMAP.md"><b>English</b></a>
</p>

ברוכים הבאים למפת הדרכים הרשמית של **RightSub**. מסמך זה מרכז את אבני-הדרך שהושלמו, סדרי העדיפויות הנוכחיים והיוזמות הארכיטקטוניות המתוכננות עבור מערך הכתוביות האוניברסלי.

---

## 🧭 סקירת התפתחות גרסאות (Milestone Progression)

```mermaid
flowchart LR
    v10["v1.0 מנוע אוטונומי"] --> v11["v1.1 חלונות ו-Seed-Safe"]
    v11 --> v12["v1.2 אוטומציית מדיה"]
    v12 --> v13["v1.3 הגהה סמנטית ו-Homebrew"]
    v13 --> v14["v1.4 ממשק TUI וקונטיינר Docker"]
    v14 --> v15["v1.5 שרת MCP וסוכנים"]

    classDef done fill:#2e7d32,stroke:#1b5e20,color:#ffffff;
    classDef planned fill:#f57f17,stroke:#e65100,color:#ffffff;
    classDef horizon fill:#1565c0,stroke:#0d47a1,color:#ffffff;

    class v10,v11,v12,v13,v14,v15 done;
```

---

## 🟢 גרסאות ששוחררו (Production Stable)

### 🌟 [גרסה 1.5.0](https://github.com/omerninyo/RightSub/releases/tag/v1.5.0) — שרת MCP מובנה, מתקין אוטומטי לסוכני AI וחבילת אשפים מאוחדת
> **תאריך שחרור:** אוקטובר 2026  
> **מסמך מפרט:** [RFC 002: שרת RightSub MCP ייעודי](docs/proposals/RFC_002_MCP_SERVER.he.md)  
> **יכולות מפתח:**
- [x] **שרת MCP רשמי (`rightsub mcp`)** ([#3](https://github.com/omerninyo/RightSub/issues/3)):
  - שרת JSON-RPC 2.0 תקני מעל `stdio` (תומך ב-Newline-Delimited JSON וב-`Content-Length`) באפס תלויות חיצוניות ועם בידוד `stdout` מוחלט.
  - חושף 8 כלי ליבה לסוכנים: `inspect_media`, `fix_plex_subtitles`, `extract_subtitles`, `prepare_translation`, `merge_and_master`, `polish_subtitles`, `audit_subtitles_qa`, ו-`transcribe_audio`.
- [x] **מתקין אוטומטי לכל סוכני ה-AI (`rightsub mcp --install`)**:
  - מזהה ורושם אוטומטית את השרת ב-**Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf** ו-**Claude Code** עם נתיבים מוחלטים, הזרקת `PATH` מלאה, גיבוי `.bak`, ושימור של 100% מהשרתים הקיימים.
- [x] **שליטה במדיה בשפה טבעית**:
  - מאפשר לכל סוכן AI לסרוק תיקיות, לתקן BiDi לפלקס עם הגנת טורנט (`Seed-Safe`), לחלץ כתוביות, לתרגם מנות ולהריץ ביקורת QA ישירות מתוך הצ'אט.

### 🌟 [גרסה 1.4.0](https://github.com/omerninyo/RightSub/releases/tag/v1.4.0) — ממשק טרמינל אינטראקטיבי (TUI), אשף התקנת Hooks וקונטיינרים
> **תאריך שחרור:** אוקטובר 2026  
> **מסמכי מפרט (RFC):**
> - [RFC 001: ממשק טרמינל אינטראקטיבי (TUI)](docs/proposals/RFC_001_INTERACTIVE_TUI.he.md)
> - [RFC 003: אשף התקנה ואבחון אוטונומי](docs/proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.he.md)
> - [RFC 004: שרת Webhook וקונטיינר Docker לחיבור Sonarr, Radarr ו-Bazarr](docs/proposals/RFC_004_DOCKER_WEBHOOK_SERVER.he.md)
> **יכולות מפתח:**
- [x] **אשף הרצה אינטראקטיבי (`rightsub` / `rightsub wizard`) ומבקר שינויים שורה-אחר-שורה (`rightsub polish --interactive`)** ([#1](https://github.com/omerninyo/RightSub/issues/1)):
  - הרצת `rightsub` ללא ארגומנטים בטרמינל או ב-CMD פותחת אוטומטית את האשף הראשי עם נירמול גרירת קבצים (`Drag & Drop` מ-Finder ומ-Windows Explorer / PowerShell) וסייר קבצים מובנה בטרמינל.
  - מבקר שינויים אינטראקטיבי (`rightsub polish --interactive`) למעבר שורה-אחר-שורה עם `[Y] אשר`, `[N] דחה`, `[E] ערוך ידנית`, `[A] אשר הכל`, `[R] דחה שארית`, והגנת `Ctrl+C`.
- [x] **מתקין אוטומטי לחיבורי תוכנות הורדה ומעטפת שירות (`rightsub setup` / `rightsub config --install-hooks`)** ([#2](https://github.com/omerninyo/RightSub/issues/2)):
  - מחולל סקריפטי סיום מוכנים עבור `qBittorrent` ו-`Transmission`, חיבור ל-`Sonarr`/`Radarr`/`Bazarr`, ומחולל שירותי רקע (`launchd` ב-macOS, `systemd --user` בלינוקס, ו-`schtasks` בחלונות).
- [x] **שרת Webhook מובנה ותמיכה רשמית בקונטיינרים (`rightsub serve` / Docker)** ([#4](https://github.com/omerninyo/RightSub/issues/4)):
  - שרת HTTP קל-משקל, תרגום נתיבים אוטונומי (`PATH_MAP`), ואימג' `Dockerfile` + `docker-compose.yml`.

### 🌟 [גרסה 1.3.0](https://github.com/omerninyo/RightSub/releases/tag/v1.3.0) — הגהה סמנטית, הפצת Bottle אוניברסלי ב-Homebrew ואשף אבחון
> **תאריך שחרור:** ספטמבר 2026  
> **יכולות מפתח:**
- [x] **הגהה ובקרת איכות סמנטית (`rightsub polish`)**: מנוע ליטוש אוטונומי לכתוביות קיימות על בסיס עקרון מרחק עריכה מינימלי (שימור 85%–90%).
- [x] **מנוע ידע היררכי (Hierarchical Domain Knowledge)**: סיווג חכם תלת-שלבי (`domain_knowledge.py`) עם חבילות ז'אנר ייעודיות ואימות עוגן דו-לשוני (**Bilingual Anchor Validation**).
- [x] **הגנת זליגת ציפייה (Forward Anticipation Drift Guard)**: פיצול קיוסים מורכבים (`split_part`) ובלימת מודל השפה מהקדמת שורות דיאלוג עתידיות.
- [x] **סנכרון חותמות זמן לכונני רשת (SMB/NAS)**: שטיפת מטא-דאטה מאולצת (`os.utime`) המונעת מלקוחות SMB ב-macOS ליפול לאפוק 2001.
- [x] **חבילת Homebrew Tap רשמית (`omerninyo/tap`)**: בקבוקים מוכנים מראש (`:all`) להתקנה בשנייה אחת על מעבדי Apple Silicon ו-Intel ללא תלות ב-Xcode.
- [x] **אשף הגדרות מהיר ואבחון בריאות מערכת**: פקודות `rightsub config` (הגדרת מפתחות ב-10 שניות) ו-`rightsub doctor` (בדיקת תלויות וסביבה).

### 🌟 [גרסה 1.2.0](https://github.com/omerninyo/RightSub/releases/tag/v1.2.0) — מערך אוטומציה לשרתי מדיה והתקנה במחשב נקי
> **תאריך שחרור:** ספטמבר 2026  
> **יכולות מפתח:**
- [x] **חיבורי מדיה מונחי אירועים (Event-Driven Hooks)**: חיבורים נקיים ובדוקים עבור qBittorrent, Sonarr, Radarr, Bazarr, Transmission ו-Tautulli/Plex.
- [x] **ארכיטקטורה ללא דמון רקע**: הוכחת 0% CPU ו-0 MB RAM במנוחה בהשוואה לדמונים כבדים.
- [x] **מדריכי התקנה מאפס**: תמיכה מלאה בהתקנה במחשבים נקיים ללא מנהלי חבילות.

### 🌟 [גרסה 1.1.0](https://github.com/omerninyo/RightSub/releases/tag/v1.1.0) — שוויון מלא ל-Windows וארכיטקטורת Seed-Safe
> **תאריך שחרור:** ספטמבר 2026  
> **יכולות מפתח:**
- [x] **תאימות מלאה לחלונות**: `rightsub.bat`, בדיקות בסביבת PowerShell והצלת קידוד Windows-1255.
- [x] **ארכיטקטורת Seed-Safe**: יצירת כתוביות צמודות ללא נגיעה בקובצי המקור בטורנטים פעילים.

### 🌟 [גרסה 1.0.0](https://github.com/omerninyo/RightSub/releases/tag/v1.0.0) — המנוע האוטונומי (`rightsub auto`)
> **תאריך שחרור:** ספטמבר 2026  
> **יכולות מפתח:**
- [x] **צינור עיבוד אוטונומי בפקודה אחת**: גילוי רצועות מוטמעות, חילוץ פרטי עלילה מ-TMDb והפקת פרומפטים.
- [x] **מנוע SubRefine**: תיקון פיסוק הפוך (BiDi RLM) ל-Plex/Infuse, ניקוי פרסומות ורעשי שמע (SDH).
- [x] **מנוע SubSwarm**: תזמור תרגום מרובה מנות בעזרת AI עם נעילת Translation Bible.

---

## 🟣 רעיונות למחקר עתידי ו-Backlog קהילתי

רעיונות הנמצאים בבדיקה וממתינים למשוב מהקהילה:
- **דשבורד Web UI מקומי**: ממשק דפדפן פשוט וקל-משקל (FastAPI / HTML5) לניהול ויזואלי של ספריית הכתוביות.
- **תמיכה רב-לשונית**: הרחבת מנגנוני ה-BiDi של SubRefine לשפות נוספות (ערבית, פרסית, ומשפחת הכתב הקירילי).
- **אימון מודל Whisper ייעודי לשמע בעברית**: כיול מודל אקוסטי מותאם לעברית לצורך תמלול שמע וסנכרון תזמונים מדויק ברמת המילי-שנייה.

---

## 📋 ניהול מפת הדרכים (Roadmap Governance)

- **הצעת רעיונות חדשים**:
  1. פתיחת דיון (Discussion) או Issue ב-GitHub.
  2. עבור תכונות מורכבות, כתיבת מפרט RFC תחת `docs/proposals/RFC_XXX_<TITLE>.md`.
  3. לאחר אישור, הרעיון משובץ ל-Milestone ייעודי ומתווסף למסמך מפת דרכים זה.
- **שלבי מחזור החיים**:
  - `Proposed`: הצעת RFC בבחינה.
  - `Planned`: מחויב לאבן-דרך רשמית בגרסה עתידית.
  - `In Progress`: בפיתוח פעיל ובדיקות יחידה.
  - `Shipped`: מוזג לענף `main`, נארז ב-Homebrew Bottle ותועד ב-`WHATS_NEW`.

</div>
