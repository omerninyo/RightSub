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

## 🛑 מה בכלל דורש AI ומה עובד 100% מקומית?

לפני שמחברים מודל שפה, **חשוב לזכור שרוב הפעולות ב-RightSub אינן זקוקות לבינה מלאכותית כלל!**

| פעולה מקומית | פקודת ה-CLI | האם דורש AI? |
| :--- | :--- | :---: |
| **זיהוי ועיבוד אוטונומי** | `./rightsub auto` | ❌ **ללא AI** (אלא אם התבקש תרגום) |
| **חילוץ כתוביות מתוך סרטי MKV/MP4** | `./rightsub extract` | ❌ **ללא AI** (מבוצע ע"י FFmpeg) |
| **תמלול קולי בשמע (quicksubs)** | `./rightsub transcribe` | ❌ **ללא LLM/API** (Apple Speech / Whisper מקומי) |
| **תיקון סימני פיסוק הפוכים לפלקס ו-BiDi** | `./rightsub fix-plex` | ❌ **ללא AI** (אלגוריתם יוניקוד RLM) |
| **המרת ג'יבריש (קידודי CP1255 ישנים)** | `./rightsub fix-plex` | ❌ **ללא AI** (מפענח קידוד אוטומטי) |
| **מחיקת פרסומות ורעשי רקע (SDH)** | `./rightsub fix-plex --clean-ads` | ❌ **ללא AI** (מסנן Regex דטרמיניסטי) |
| **תיקון בריחת סנכרון פריימים (FPS)** | `./rightsub adjust-fps` | ❌ **ללא AI** (חישוב מתמטי) |
| **סנכרון שמע מדויק לכתוביות מוסטות** | `./rightsub audio-sync` | ❌ **ללא AI** (אלגוריתם התאמת פונמות) |
| **איחוד מנות מתורגמות ל-SRT סופי** | `./rightsub merge` | ❌ **ללא AI** (חיבור תזמונים והזרקת RLM) |
| **ביקורת איכות סופית (QA)** | `./rightsub qa` | ❌ **ללא AI** (ספירה ובדיקת התאמה 1:1) |
| **תרגום שורות הדיאלוג עצמן מאנגלית לעברית** | `./rightsub prompt-gen` / `translate-ollama` | 🧠 **שלב ה-AI היחיד!** |

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

## 🛠️ מדריכי הפעלה לפי כלי AI פופולריים

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
