<div dir="rtl">

# מפרט ארכיטקטוני לפיתוח עתידי: שרת RightSub MCP (Model Context Protocol)

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="MCP-Server-Specification"><b>English</b></a>
</p>

מסמך זה מתעד את עקרונות התכנון, מבנה הכלים והארכיטקטורה להפיכת **RightSub** לשרת **MCP (Model Context Protocol)**. מטרת הפרויקט היא לחבר את כלי הליבה של RightSub ישירות ליישומי וסוכני AI מובילים (כגון Claude Desktop, Antigravity, Cursor ו-ChatGPT), ובכך לספק ממשק שיחה טבעי ואינטראקטיבי לחלוטין לצד תרגום כתוביות באיכות הגבוהה ביותר בענן.

---

## 1. רציונל הנדסי ומטרות הפרויקט (Rationale & Objectives)

1. **ממשק משתמש טבעי (Natural Language as UI):**
   - במקום לפתח ממשק גרפי (GUI) או ללמוד פקודות טרמינל, המשתמש מנהל שיחה טבעית בצ'אט: *"הורדתי סרט חדש, תבדוק אם יש לו כתוביות בעברית ותעזור לי לתרגם אם חסר"*.
2. **פתרון מוחלט לכשל התרגום המקומי בעברית:**
   - מודלים מקומיים קטנים (Llama 3.2, Qwen 2.5) נכשלו לחלוטין בתרגום כתוביות לעברית עקב קריסת תפיסת מגדר, תחביר עילג ופירוק טוקנים לבייטים.
   - במודל MCP, הסוכן בצ'אט מופעל על ידי מודלי ענן מובילים (כמו Claude 3.5 Sonnet או Gemini 2.0 Pro). הסוכן מקבל את מנות הכתוביות המובנות מ-RightSub, מתרגם אותן בעצמו באיכות שידור מקצועית, ומחזיר אותן למערכת למיזוג.
3. **עבודה חופשית עם קובצי מדיה כבדים (Local-First Media Processing):**
   - קובצי סרטים שוקלים 2GB עד 30GB ולא ניתן להעלותם לרשת. שרת MCP רץ מקומית על המחשב מעל `stdio` ומפעיל את FFmpeg ישירות בדיסק המקומי. חילוץ הכתובית אורך כ-0.2 שניות, ורק טקסט הכתובית הזעיר (כ-50KB) מועבר למודל השפה.
4. **ניהול מפתחות שקוף:**
   - המשתמש אינו צריך לרכוש או לנהל מפתחות API נוספים של AI עבור RightSub – הוא משתמש בחיבור הצ'אט הקיים של יישום ה-AI שלו.

---

## 2. ארכיטקטורת התקשורת (Transport & Protocol Architecture)

- **פרוטוקול:** Model Context Protocol (MCP) מבית Anthropic.
- **ערוץ תקשורת (Transport):** `stdio` (Standard Input / Standard Output) עם הודעות JSON-RPC מקומיות.
- **אבטחה:** השרת רץ כתהליך בן (Subprocess) של יישום ה-AI. אין פורטים פתוחים ברשת ואין חשיפה של קבצים מחוץ לספריות המורשות.
- **פקודת הפעלה:** `./rightsub mcp` או `python3 -m rightsub.mcp`.

---

## 3. מפרט כלי ה-MCP המוצעים (Tools Specification)

שרת ה-MCP יחשוף לסוכן ה-AI סדרה של כלים מוגדרים היטב:

### א. `inspect_media(path: str)`
- **תיאור:** בודק קובץ וידאו, קובץ כתוביות או תיקיית מדיה ומחזיר תמונת מצב מובנית.
- **פלט:**
  - האם קיימת כתובית עברית חיצונית ומה הקידוד שלה (CP1255 / UTF-8).
  - האם קיימת כתובית עברית מוטמעת בתוך קובץ הווידאו.
  - האם קיימות כתוביות אנגליות לחילוץ.
  - האם נדרש תיקון BiDi/RLM לפלקס.

### ב. `fix_plex_subtitles(path: str, replace_original: bool = False)`
- **תיאור:** מפעיל את מנוע `SubRefine` על כתובית עברית.
- **פעולות:** תיקון סימני פיסוק, הזרקת RLM, המרת קידוד ל-UTF-8 נקי, ניקוי ספאם ופרסומות.
- **מדיניות טורנטים:** פועל במצב Seed-Safe כברירת מחדל (משכפל ל-`<stem>.he.srt` ומשאיר את המקור ללא שינוי).

### ג. `extract_subtitles(video_path: str, lang: str = "eng", output_path: str = None)`
- **תיאור:** מפעיל את מנוע החילוץ (FFmpeg) על קובץ הווידאו ומייצר קובץ `.srt` חיצוני מקור.

### ד. `prepare_translation(srt_path: str, enrich_tmdb: bool = True)`
- **תיאור:** מכין את תשתית התרגום עבור סוכן ה-AI.
- **פעולות:**
  - זיהוי הסרט/סדרה ותשאול TMDb לזיהוי שמות הדמויות, המגדר ותקציר העלילה.
  - יצירת מילון מונחים (`translation_bible.json`).
  - פיצול הכתובית למנות JSON ממוספרות עם הקשר רציף (Context Overlap).
- **פלט:** נתיב למנות התרגום ומילון המונחים שהסוכן צריך לתרגם.

### ה. `merge_and_master(en_srt_path: str, translated_batches_dir: str, output_path: str)`
- **תיאור:** מקבל את מנות ה-JSON המתורגמות מהסוכן, מוודא התאמת 1:1 של כל האינדקסים והזמנים, מחיל RLM, ומייצר קובץ `.he.srt` סופי.

### ו. `transcribe_audio(video_path: str)`
- **תיאור:** מפעיל תמלול קולי (Speech-to-Text) מקומי כאשר אין כתוביות מוטמעות בווידאו (מזהה אוטומטית תמיכה ב-Apple Silicon ב-macOS).

### ז. `audit_subtitles_qa(en_srt_path: str, he_srt_path: str, strict_gender: bool = False)`
- **תיאור:** מפעיל בדיקת איכות מלאה (Red Team QA) להשוואת המקור מול התרגום (אינדקסים, פערי זמנים ובדיקת מגדר דמויות).

---

## 4. תרחיש שימוש מלא (End-to-End User Experience)

```text
משתמש (בתוך Claude Desktop / Antigravity):
"הורדתי את הסרט /Volumes/Media/Gladiator (2000)/Gladiator.mkv. 
תוודא שיש כתוביות עברית תקינות לפלקס, ואם אין – תחלץ את האנגלית ותעזור לי לתרגם."

סוכן ה-AI (מבצע קריאות כלים ברקע):
1. קריאה ל-inspect_media:
   <- תוצאה: אין כתובית עברית, יש כתובית אנגלית מוטמעת מס' 2.
2. קריאה ל-extract_subtitles:
   <- תוצאה: נוצר Gladiator.en.srt מקומית.
3. קריאה ל-prepare_translation:
   <- תוצאה: נמשכו מ-TMDb דמויות ומגדר (Maximus: Male, Lucilla: Female), נוצרו מנות תרגום.
4. הסוכן מתרגם בעצמו את מנות ה-JSON ישירות בצ'אט תוך הקפדה על המגדר.
5. קריאה ל-merge_and_master:
   <- תוצאה: נוצר Gladiator.he.srt מושלם ותקני לפלקס.
6. קריאה ל-audit_subtitles_qa:
   <- תוצאה: 0 שגיאות, 100% התאמת שורות.

תשובת הסוכן למשתמש:
"הסרט Gladiator טופל בהצלחה!
לא נמצאה כתובית עברית, לכן חילצתי את האנגלית מתוך קובץ הווידאו, תרגמתי אותה לעברית תקנית 
(תוך הקפדה על פנייה נכונה לדמויות לפי TMDb), ויצרתי קובץ מוכן Gladiator.he.srt שמוכר מיד בפלקס."
```

---

## 5. הגדרת התקנה בקליינט (Configuration Example)

המשתמש יוסיף את ההגדרה הבאה לקובץ הקונפיגורציה של סוכן ה-AI שלו (למשל `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rightsub": {
      "command": "python3",
      "args": ["/path/to/RightSub/rightsub.py", "mcp"],
      "env": {
        "TMDB_API_KEY": "YOUR_OPTIONAL_TMDB_KEY"
      }
    }
  }
}
```

---

## 6. טכנולוגיות ומימוש מוצע (Implementation Stack)

- שימוש בספרייה הרשמית של Anthropic ל-Python: `mcp` או `fastmcp`.
- השרת ממומש בקובץ ליבה ייעודי `src/mcp_server.py`.
- כל הכלים קוראים ישירות לפונקציות הליבה שכבר נבדקו ואומתו במערכת, ללא שכפול קוד.

---

## 7. מעקב גרסאות ומפת דרכים

- **יעד גרסה:** 1.5.0
- **מיילסטון ב-GitHub:** [`v1.5.0 — Agentic Subtitle Protocol & MCP Server`](https://github.com/omerninyo/RightSub/milestone/2)
- **כרטיס מעקב (Issue):** [#3](https://github.com/omerninyo/RightSub/issues/3)
- **מפת דרכים:** [מפת דרכים ומעקב אבני-דרך](מפת-דרכים)

</div>
