<div dir="rtl">

# ברוכים הבאים ל-Wiki של RightSub

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="Home"><b>English</b></a>
</p>

**RightSub** היא סוויטת כלי CLI וספריית פייתון ברמת Production, שתוכננה עבור **Windows** ועבור **macOS** במטרה לתקן, להשביח, לנקות, לסנכרן ולתרגם כתוביות עבור **כל סרט וכל סדרת טלוויזיה**.

---

## ⚡ התחלה מהירה ב-30 שניות

יש לכם קובץ כתוביות או וידאו שצריך לתקן או לתרגם? ב-**RightSub v1.5.0** עומדות לרשותכם 3 דרכים פשוטות:

1. **אשף הפעלה אינטראקטיבי (ללא דגלים כלל):** הקלידו `rightsub` בלבד כדי לפתוח תפריט אינטראקטיבי עם תמיכה בגרירת קבצים (Drag & Drop) ודפדפן קבצים מובנה (`[B] Browse`).
2. **פקודת-על אוטונומית (`rightsub auto`):**
   - **Windows (CMD / PowerShell):** `rightsub auto "C:\Movies\Inception.srt"`
   - **macOS / Linux (Terminal):** `rightsub auto ~/Movies/Inception.srt`
3. **חיבור בלחיצה אחת לסוכני AI (שרת MCP מובנה):** הריצו `rightsub mcp --install` לרישום אוטומטי ב-**Google Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf** ו-**Claude Code**.

---

## 📚 מפתח המדריכים המלא ב-Wiki

- 🔰 **[מדריך פשוט למתחילים](מדריך-פשוט-למתחילים)**: צעד אחר צעד ללא מושגים טכניים (אשף אינטראקטיבי, תיקון לפלקס ותרגום מהיר).
- 📦 **[מדריך התקנה והפצה](מדריך-התקנה-והפצה)**: התקנת Homebrew Tap, מתקין Windows (`install.bat`), `rightsub setup` ו-`rightsub mcp --install`.
- 🤖 **[מדריך חיבור לכלי בינה מלאכותית](מדריך-חיבור-לכלי-בינה-מלאכותית)**: שרת MCP מובנה (`rightsub mcp`), הפרדה בין תיקון טכני (`0` טוקנים ב-99% מהמקרים) לבין תרגום מלא.
- 📐 **[מדריך כיווניות BiDi ופלקס](מדריך-BiDi-ופלקס)**: הסבר מעמיק על תו ה-RLM (`\u200F`), תקן UAX #9 Rule N1 וביטול 18 תבניות היפוך ויזואליות.
- 💎 **[מפרט מנוע ליטוש סמנטי ובקרת איכות](מפרט-מנוע-ליטוש-סמנטי-ובקרת-איכות)**: הגהה סמנטית, תיקון מספרים דו-לשוני וסקירה אינטראקטיבית שורה-אחר-שורה (`--interactive`).
- 🔄 **[מדריך אינטגרציות ואוטומציה לשרתי מדיה](מדריך-אינטגרציות-ואוטומציה)**: חיבור אוטומטי ל-qBittorrent, Sonarr, Radarr, Bazarr, Transmission וקונטיינר Docker (`rightsub serve`).
- ⚖️ **[השוואה טכנית מול Bazarr](השוואה-מול-Bazarr)**: ניתוח ברמת קוד המקור ושילוב מומלץ.
- 🎙️ **[תמלול וסנכרון מקומי מונחה אודיו](תמלול-וסנכרון-מקומי-quicksubs)**: תמלול מקומי ללא ענן באמצעות מנוע quicksubs.
- 🎬 **[אינטגרציית TMDb](אינטגרציית-TMDb)**: שיוך מגדרי דטרמיניסטי, שחקני אורח והכנת דיאלקט.
- 🔄 **[תהליך עבודה מלא מקצה לקצה](תהליך-עבודה)**: זרימת עבודה מלאה מווידאו גולמי לכתובית מושלמת.
- 🗺️ **[מפת דרכים](מפת-דרכים)** ו-🚀 **[מה חדש (`v1.5.0`)](מה-חדש)**: היסטוריית גרסאות ומעקב אבני-דרך.
- 🏆 **[מקרה בוחן בוסטון ליגל (תיאורטי)](מקרה-בוחן-בוסטון-ליגל)**: בנצ'מרק אימות אלגוריתמי על 101 פרקים ומעל 78,000 כתוביות.

---

## 🏛️ שני מנועי הליבה

RightSub מפרידה באופן מודולרי בין ממשק הפקודות (CLI) לבין שני מנועי הליבה שלה:

1. **מנוע SubRefine**:
   - **תיקון BiDi ל-Plex ו-Infuse**: הזרקת RLM (`\u200F`) למניעת היפוכי פיסוק ב-Apple TV, Android TV, Infuse ו-VLC.
   - **ניקוי רעשי שמע (SDH)**: הסרת תיאורי שמיעה (`[מחיאות כפיים]`, `♪ מוזיקה ♪`) תוך שמירה על התזמון.
   - **המרת קידוד**: זיהוי אוטומטי של קידודי עברית ישנים (CP1255 / Windows-1255) והמרה ל-UTF-8.
   - **נרמול הומוגליפים וטיפוגרפיה**: תיקון אותיות קיריליות/ערביות והמרת גרשיים תקניים בראשי תיבות (`עו״ד`, `ארה״ב`).
   - **מתיחת פריימים וסנכרון**: מתיחה אוטומטית מ-25.0 ל-23.976 FPS והתאמת זמנים.

2. **מנוע SubSwarm**:
   - **גלי סוכנים מקבילים**: תרגום מקבילי באמצעות Google Gemini 3.5 Flash-Lite או Ollama מקומי.
   - **Translation Bible**: הפקת מילון מונחים, שמות דמויות ומגדר מתוך TMDb.
   - **ערבות התאמת 1 ל-1**: אפס שורות שנשמטות, אפס תזמונים שמתחברים, אפס הזיות.

---

## 💻 מדריך פקודות CLI מלא (`v1.5.0`)

| פקודה | מנוע אחראי | תיאור | דוגמה ב-Windows | דוגמה ב-macOS / Linux |
| :--- | :---: | :--- | :--- | :--- |
| `rightsub` *(ללא דגלים)* / `wizard` | **TUI** | אשף הפעלה אינטראקטיבי (גרירת קבצים + דפדפן קבצים מובנה) | `rightsub` | `rightsub` |
| `setup` | **ליבה** | אשף התקנה ראשונית, יצירת Hooks ל-qBittorrent/Sonarr ושירותי רקע | `rightsub setup` | `rightsub setup` |
| `mcp` | **MCP** | שרת MCP מקומי (JSON-RPC 2.0) ומתקין אוטומטי לסוכני AI | `rightsub mcp --install` | `rightsub mcp --install` |
| `auto` | **הכל** | הפעלה אוטונומית שלמה (קובץ בודד, עונה או תיקייה) | `rightsub auto "Movie.mkv"` | `rightsub auto "Movie.mkv"` |
| `polish` | **שניהם** | הגהה וליטוש סמנטי, תיקון קאנון/מספרים וסקירה אינטראקטיבית (`-i`) | `rightsub polish "Movie.he.srt" -i` | `rightsub polish "Movie.he.srt" -i` |
| `serve` | **Daemon** | שרת Webhook לקונטיינרים ולמארח עבור Sonarr, Radarr ו-Bazarr | `rightsub serve --port 8775` | `rightsub serve --port 8775` |
| `translate-ollama` | **SubSwarm** | תרגום מקומי 100% חינמי ואופליין דרך Ollama | `rightsub translate-ollama prompts` | `rightsub translate-ollama prompts` |
| `fix-plex` | **SubRefine** | תיקון פיסוק, RLM, קידוד CP1255, ניקוי SDH וספאם | `rightsub fix-plex ./Season1/ -r -i` | `rightsub fix-plex ./Season1/ -r -i` |
| `adjust-fps` | **SubRefine** | מתיחת פריימים (25 <-> 23.976) או הזזת אופסט | `rightsub adjust-fps in.srt -o out.srt` | `rightsub adjust-fps in.srt -o out.srt` |
| `extract` | **SubRefine** | חילוץ כתוביות מווידאו (MKV/MP4) בעזרת FFmpeg | `rightsub extract video.mp4 -o out.srt` | `rightsub extract video.mp4 -o out.srt` |
| `transcribe` | **quicksubs** | תמלול קולי מהיר ישירות מהשמע (Apple Speech / Whisper) | `rightsub transcribe video.mp4` | `rightsub transcribe video.mp4` |
| `audio-sync` | **quicksubs** | סנכרון וכיול כתוביות מוסטות על בסיס ציר השמע | `rightsub audio-sync bad.srt -v v.mp4 -o ok.srt` | `rightsub audio-sync bad.srt -v v.mp4 -o ok.srt` |
| `sync` | **SubRefine** | השוואת תזמונים בין כתובית מקור לכתובית חיצונית | `rightsub sync master.en.srt dl.he.srt` | `rightsub sync master.en.srt dl.he.srt` |
| `bible` | **SubSwarm** | הפקת Translation Bible (דמויות, מונחים ומגדר מ-TMDb) | `rightsub bible Season1/*.srt -o b.json --tmdb` | `rightsub bible Season1/*.srt -o b.json --tmdb` |
| `split` | **SubSwarm** | פיצול SRT באנגלית למנות JSON של כ-210 שורות | `rightsub split ep.en.srt -o ./batches/` | `rightsub split ep.en.srt -o ./batches/` |
| `prompt-gen` | **SubSwarm** | מחולל פרומפטים וגלי סוכנים עם מילון דמויות וחפיפה | `rightsub prompt-gen ep.en.srt -t "Inception"` | `rightsub prompt-gen ep.en.srt -t "Inception"` |
| `config` | **ליבה** | אשף הגדרת מפתחות API, מתקין Hooks (`--install-hooks`) ושירותי רקע | `rightsub config --install-hooks` | `rightsub config --install-hooks` |
| `doctor` | **ליבה** | דשבורד אבחון ובדיקת בריאות לתלויות, שירותים וסוכני MCP | `rightsub doctor` | `rightsub doctor` |
| `merge` | **שניהם** | מיזוג מנות תרגום ל-SRT סופי עם הזרקת RLM מלאה | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` |
| `qa` | **שניהם** | דוח בקרת איכות של 1-לאחד, טיהור תווים זרים ומגדר | `rightsub qa ep.en.srt ep.he.srt` | `rightsub qa ep.en.srt ep.he.srt` |

</div>
