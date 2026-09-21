<div dir="rtl">

# תמלול מקומי On-Device וסנכרון מונחה שמע (אינטגרציית quicksubs)

פרויקט RightSub משלב את **`quicksubs`**, כלי שורת פקודה מתקדם לתמלול מקומי על גבי macOS שפותח על ידי **Matt Birchler**.

- **מחבר**: Matt Birchler
- **מאגר GitHub**: [mattbirchler/quicksubs](https://github.com/mattbirchler/quicksubs)
- **אתר המחבר**: [Birchtree](https://birchtree.me)
- **אפליקציית Mac מקבילה**: [Quick Subtitles](https://quickstuff.app)

---

## סקירה כללית

השילוב עם `quicksubs` מעניק ל-RightSub יכולות Speech-to-Text מקומיות ישירות על גבי החומרה של ה-Mac:

1. **חילוץ ותמלול מקור כשאין כתוביות (תרחיש 1)**: תמלול אוטומטי של קובצי וידאו ואודיו לכתוביות `.srt` תקניות.
2. **סנכרון תזמונים מונחה שמע (תרחיש 2)**: כיול מחדש של כתוביות שיצאו מסנכרון באמצעות תזמוני עוגן אמיתיים מרצועת השמע.

---

## התקנה ב-macOS

```bash
brew install mattbirchler/tap/quicksubs
```

---

## מנועי תמלול מקומיים נתמכים

| מנוע | דגל הפעלה | משקל מודל | תיאור |
| :--- | :--- | :--- | :--- |
| **Apple SpeechAnalyzer** | `--engine apple` | 0 MB (מובנה) | רץ ישירות על ה-Neural Engine של Apple Silicon (ברירת מחדל). |
| **OpenAI Whisper** | `--engine whisper` | ~626 MB | דיוק מקסימלי לתכנים מורכבים. |
| **NVIDIA Parakeet** | `--engine parakeet` | ~400 MB | מודל עצבי מקומי קל ומהיר. |

---

## פקודות ושימוש

### 1. תמלול ישיר
```bash
python3 scripts/00_transcribe_audio.py "/path/to/video.mp4" -e apple
```

### 2. חילוץ כתוביות עם Fallback אוטומטי
```bash
python3 scripts/01_extract_subtitles.py "/path/to/videos" --transcribe --engine apple
```

### 3. סנכרון תזמונים מונחה שמע
```bash
python3 scripts/16_audio_align_sync.py "unsynced.he.srt" -o "aligned.he.srt" -v "video.mp4"
```

---

## מפת דרכים עתידית

- **מזעור רוחב פס ועלויות ענן**: תמלול מקומי בחינם, ומשלוח כתוביות טקסט בלבד ל-Gemini.
- **אוטומציית רקע לשרת מדיה**: LaunchAgent ב-macOS לניטור תיקיות הורדה ויצירת כתוביות אוטומטית.
- **תמלול פודקאסטים והקלטות קוליות**: עיבוד ישיר של הקלטות לטקסט ולכתוביות.
- **מדידת ביצועי Apple Silicon**: הרצת `quicksubs bench` להשוואת מהירויות בין מעבדים.

</div>
