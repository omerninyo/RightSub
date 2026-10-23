<div dir="rtl">

# 🤖 מדריך חיבור לכלי בינה מלאכותית וסייעני קוד (AI Integration Guide)

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="AI_INTEGRATION_GUIDE.md"><b>English</b></a>
</p>

ברוכים הבאים למדריך החיבור והאינטגרציה של **RightSub** עם כלי בינה מלאכותית (AI) וסייעני קוד מודרניים (**Google Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, **Gemini CLI**, **ChatGPT** ועוד).

מדריך זה מספק:
1. **תבניות פרומפטים מוכנות להעתקה ולהדבקה** שתוכלו לתת לכל סוכן AI כדי שיבצע את העבודה עבורכם.
2. **הנחיות מערכת (System Instructions)** שתוכלו להדביק ב-`.cursorrules`, `.claude.md`, או בהגדרות הסוכן כדי שילמד להפעיל את RightSub באופן אוטונומי.
3. **הסבר על תרגום מקומי בחינם דרך Ollama** ללא מפתחות API וללא אינטרנט.

---

## 📋 תבניות פרומפטים מוכנות להעתקה (Copy-Paste Prompt Templates)

פשוט העתיקו את הפרומפט המתאים והדביקו בחלון השיחה מול סוכן ה-AI שלכם (למשל Antigravity, Claude Code או Cursor):

### תבנית 1: תיקון כתוביות עברית לפלקס (Plex / Infuse)
> *"אנא השתמש בכלי RightSub כדי לסרוק ולתקן את כל קובצי הכתוביות בעברית בתיקייה [נתיב לתיקייה]. ודא שסימני הפיסוק (BiDi) מיושרים לפלקס, מחק שורות פרסומות וספאם, ושמור גיבוי .bak לפני כל שינוי."*

### תבנית 2: תרגום מלא של סרט או עונה שלמה מאנגלית לעברית
> *"אנא השתמש ב-RightSub כדי לעבד את קובץ הווידאו [נתיב לקובץ]. אם אין כתוביות באנגלית - חלץ אותן או תמלל אותן באמצעות quicksubs. הכן את מנות התרגום, תרגם אותן בעברית טבעית ברמת שידור עם שמירה על מגדר הדמויות, ומזג לקובץ סופי [שם].he.srt תואם פלקס."*

### תבנית 3: הפעלה אוטונומית מקומית עם Ollama (ללא API וללא עלות)
> *"אנא הרץ את פקודת העל של RightSub עם מודל מקומי: `./rightsub auto "[נתיב לקובץ או תיקייה]" --ollama`. עקוב אחר ההתקדמות ודווח לי כשהקובץ הסופי מוכן."*

### תבנית 4: בדיקת בקרת איכות וסנכרון תזמונים (QA & Timing Audit)
> *"אנא הרץ בדיקת איכות QA בין קובץ האנגלית [Movie.en.srt] לקובץ העברית [Movie.he.srt] באמצעות `./rightsub qa`. ודא שאין פערי תזמונים או כתוביות חסרות ודווח לי על הממצאים."*

---

## 🛠️ הנחיות מערכת מובנות לסוכני AI (Agent System Prompt / Rule)

רוצים שסוכן ה-AI שלכם יכיר את RightSub באופן קבוע בכל פעם שאתם פותחים פרויקט?  
העתיקו את בלוק הקוד הבא לתוך קובץ `.cursorrules`, `.claude.md`, או כהנחיית רקע בסוכן שלכם:

```markdown
# RightSub CLI Agent Instructions

You have access to the `RightSub` CLI tool in this workspace (`./rightsub`).
RightSub is an enterprise-grade subtitle translation, mastering, and BiDi engine for Plex/Infuse.

Key CLI Commands to execute tasks on behalf of the user:
1. Autonomous runner (Recommended for all single files or folders):
   `./rightsub auto "<path_to_video_or_srt_or_dir>"`
   Options:
   - `--ollama`: Perform 100% offline local translation using local Ollama instance.
   - `--dry-run`: Preview without writing changes.

2. Hebrew Plex & BiDi Repair:
   `./rightsub fix-plex "<path>" --in-place --clean-ads --backup`
   Recursively:
   `./rightsub fix-plex "<directory>" --recursive --in-place --clean-ads --backup`

3. Translation Batches & Bible Generation:
   `./rightsub bible "<file.en.srt>" -o "translation_bible.json" --tmdb`
   `./rightsub prompt-gen "<file.en.srt>" -t "<Title>" -b "translation_bible.json" -o "prompts_<Title>"`

4. Merge Translated Batches into Hebrew SRT:
   `./rightsub merge "<file.en.srt>" "prompts_<Title>" -o "<Title>.he.srt"`

5. Quality Assurance (QA):
   `./rightsub qa "<file.en.srt>" "<Title>.he.srt"`

6. Speech-to-Text Transcription (when video lacks subtitles):
   `./rightsub transcribe "<video_path>" -o "<output_dir>"`

Rules:
- Always use `./rightsub auto` when the user requests a simple or hands-off operation.
- Always preserve cue numbers and timestamps when translating subtitle batches.
- When generating Hebrew dialogue, ensure proper BiDi formatting and use Hebrew gershayim (״) for acronyms.
```

---

## 🛑 מה דורש AI ומה עובד 100% מקומית? (מטריצת ההכרעה לפי קיום מפתח AI)

**99% מפעולות תיקון הכתוביות ב-RightSub אינן משתמשות בבינה מלאכותית כלל.** המערכת מפרידה באופן קשיח בין תיקון טכני דטרמיניסטי לבין פעולות מבוססות-מודל בהתאם לסוג המשימה והאם המשתמש הזין מפתח AI:

| פעולה | פקודת ה-CLI | ללא מפתח AI (ברירת המחדל) | עם מפתח AI (`GEMINI_API_KEY` / `--ollama`) |
| :--- | :--- | :---: | :---: |
| **זיהוי תוכן עברי בכל `.srt` והגנת טורנט (`Seed-Safe` $\rightarrow$ `.he.srt`)** | `./rightsub auto` | ✅ **100% דטרמיניסטי (0 AI)** — מזהה עברית בתוך כל `.srt`, משאיר את המקור לטורנט, ושומר `.he.srt` נפרד | זהה (0 AI על כתוביות קיימות) |
| **מנוע BiDi תלת-שלבי, `UAX #9 Rule N1` והיפוך תבניות `Subabi`** | `./rightsub fix-plex` / `auto` | ✅ **100% דטרמיניסטי (0 AI)** | זהה (לעולם לא מערב AI) |
| **הצלת קידוד (`CP1255` $\rightarrow$ `UTF-8`) וניקוי `Homoglyphs` זרים** | `./rightsub fix-plex` / `auto` | ✅ **100% דטרמיניסטי (0 AI)** | זהה (לעולם לא מערב AI) |
| **הצלבת מספרים דו-לשונית (`84` $\rightarrow$ `48` מול `.en.srt`) ובדיקת `Cue Drift`** | `./rightsub merge` / `polish` | ✅ **100% דטרמיניסטי (0 AI)** | זהה (רץ אוטומטית לפני כל שלב מודל) |
| **חילוץ כתוביות (`FFmpeg`) ותמלול שמע מקומי (`quicksubs`)** | `./rightsub extract` / `transcribe` | ✅ **100% מקומי (0 טוקנים)** | זהה |
| **תיקון פריימים (`adjust-fps`), סנכרון שמע (`audio-sync`) וביקורת (`qa`)** | `./rightsub qa` | ✅ **100% דטרמיניסטי (0 AI)** | זהה |
| **ליטוש כתוביות קיימות (למקרי קצה נדירים בלבד)** | `./rightsub polish` | ✅ **מעבר קאנון ומספרים דטרמיניסטי אופליין (0 AI)** | 🧠 **הגהה סמנטית מבוססת AI** *(מיועד אך ורק למקרים נדירים: תרגומים ישנים מאוד, משובשי OCR או תרגומי מכונה ירודים)* |
| **תרגום מאפס מאנגלית לעברית (`EN` $\rightarrow$ `HE`)** | `./rightsub prompt-gen` / `auto` | מפיק מנות פרומפטים להדבקה בצ'אט ה-AI | 🧠 **תרגום מלא מבוסס AI** |

> [!IMPORTANT]
> **מתי באמת צריך מפתח AI על כתוביות קיימות?**
> - **בכתוביות אנושיות רגילות (99% מהמקרים):** לעולם לא. הרצת `rightsub auto` או `rightsub fix-plex` מתקנת את כל בעיות הפיסוק, ה-BiDi, הקידוד והיפוכי ה-`Subabi` באופן דטרמיניסטי עם **0 טוקנים**, תוך שמירה מלאה על קובץ ה-`.srt` המקורי של הטורנט ויצירת `.he.srt` נפרד.
> - **בכתוביות ישנות מאוד / משובשות OCR / תרגומי מכונה ירודים (~1% מהמקרים):** רק כאשר הקובץ העברי הקיים הוא תרגום מכונה גולמי או חילוץ OCR משובש (`PGS`/`VobSub`) עם שגיאות מגדר קשות לאורך הדיאלוג, יש טעם להריץ `rightsub polish` עם מפתח AI.

---

## 🦙 תרגום מקומי עם Ollama (גיבוי אופליין / ניסיוני)

> [!WARNING]
> **ניתוח טכני: מדוע מודלים מקומיים (7B/8B) אינם מתאימים לתרגום עברית ברמת שידור?**
> 
> אף ש-RightSub תומכת טכנית בחיבור ל-Ollama, יש להבין את המגבלות המבניות של מודלים פתוחים בעברית:
> 1. **פרגמנטציית טוקניזציה (Byte-Fallback Fragmentation):**  
>    הטוקנייזרים של Llama 3, Mistral ומודלי קוד פתוח דומים כמעט ואינם מכילים מילים או מורפמות בעברית. כל אות עברית מפורקת ל-2 עד 3 טוקנים של בייטים גולמיים ב-UTF-8. הדבר גורם לצריכת טוקנים מהירה, איטיות ניכרת, ופגיעה חמורה בהבנת ההקשר התחבירי.
> 2. **ייצוג מזערי בדאטה (פחות מ-0.1%):**  
>    המודלים אינם שולטים בסלנג, ביטויים אידיומטיים ותרבותיים, ומפיקים "עברית מכנית" ותרגום מילולי עילג.
> 3. **קריסה בהתאמה מגדרית (Gender Agreement):**  
>    עברית מחייבת הבחנה קפדנית בין פנייה לזכר ("אתה", "ראית") לנקבה ("את", "ראית"). מודלי 8B שוגים בעקביות ומערבבים מגדרים בדיאלוגים.
> 
> **שורה תחתונה:** מודל מקומי מתאים אך ורק כמסלול גיבוי אופליין מלא כשאין גישה לרשת. לתרגום מקצועי של סרטים וסדרות, **מומלץ בחום להשתמש במודלי ענן חזקים (Gemini Flash / Pro, Claude 3.5 Sonnet, GPT-4o)** המאומנים על מאגרי ענק בעברית ומספקים דיוק דקדוקי מלא.

### הרצה מקומית לגיבוי אופליין:
1. ודאו ש-Ollama מותקן ופועל במחשב שלכם (`ollama serve`).
2. הריצו תרגום ישיר של תיקיית מנות שהוכנה:
   ```bash
   ./rightsub translate-ollama "prompts_Movie" --en-srt "Movie.en.srt" -o "Movie.he.srt"
   ```

---

## 🛠️ מדריכי הפעלה לפי כלי AI וחיבור MCP אוטומטי בפקודה אחת

### 0. חיבור אוטומטי של שרת ה-MCP לכל סוכן (`rightsub mcp --install` — מומלץ)
במקום להעתיק קובצי פרומפטים ידנית, חברו את שרת ה-**MCP (Model Context Protocol)** המובנה של RightSub ישירות לכל סוכני ה-AI שלכם (**Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf** ו-**Claude Code**) בפקודה אחת:
```bash
# זיהוי ורישום אוטומטי בכל סוכני ה-AI המותקנים במחשב:
rightsub mcp --install

# או רישום בסוכן ספציפי בלבד:
rightsub mcp --install --agent claude
rightsub mcp --install --agent cursor

# בדיקת סטטוס החיבור בכל הסוכנים:
rightsub mcp --status
```
לאחר הרישום, הסוכן מקבל גישה ישירה ל-8 כלי הליבה (`inspect_media`, `fix_plex_subtitles`, `extract_subtitles`, `prepare_translation`, `merge_and_master`, `polish_subtitles`, `audit_subtitles_qa`, `transcribe_audio`) ויכול לבדוק, לתקן או לתרגם כל תיקיית מדיה מתוך שיחה רגילה.

### 1. Google Antigravity (מומלץ ביותר — סביבת ברירת המחדל)
פשוט כתבו לסוכן בשיחה:
> *"הרץ את `./rightsub auto` על קובץ הווידאו שלי, הכן מנות תרגום, הפעל סוכני משנה (Subagents) במקביל כדי לתרגם את המנות, ומזג לקובץ סופי."*

### 2. Claude Code CLI (Anthropic)
בתוך הטרמינל עם `claude`:
> *"קרא את `prompts_Movie/batch_01_prompt.txt` ותרגם את `batch_01_input.json` לקובץ `batch_01_translated.json` במבנה JSON זהה."*

### 3. עורכי AI: Cursor ו-Windsurf
פתחו את התיקייה ב-Cursor, פתחו את ה-Composer (`Cmd+I`):
> *"קרא את קובצי המנות ב-`prompts_Movie`, תרגם כל מנה לקובץ `batch_XX_translated.json` התואם, והרץ `./rightsub merge` בסיום."*

---

## 🎯 כלל הזהב של המיזוג הסופי

לא משנה באיזה כלי בינה מלאכותית בחרתם לתרגם את הטקסט — **סיום התהליך תמיד נעשה מקומית ב-100% דיוק:**

```bash
# 1. מיזוג המנות לקובץ כתוביות עברי מסונכרן:
./rightsub merge "Movie.en.srt" "prompts_Movie" -o "Movie.he.srt"

# 2. הרצת בדיקת בקרת איכות אוטומטית (QA):
./rightsub qa "Movie.en.srt" "Movie.he.srt"
```

</div>
