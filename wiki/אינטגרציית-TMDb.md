<div dir="rtl">

# אפיון עלילה, דמויות, מגדר ודיאלקט (אינטגרציית TMDb)

פרויקט RightSub משלב את ממשק ה-API של **The Movie Database (TMDb)** לצורך זיהוי עובדתי ודטרמיניסטי של דמויות, שיוך מגדרי מדויק לשחקני אורח, חילוץ תקצירי עלילה והזרקת הנחיות דיאלקט (בריטי/אמריקאי) ומשלב לשוני.

- **ספק נתונים**: [The Movie Database (TMDb)](https://www.themoviedb.org)
- **תיעוד API רשמי**: [TMDb API Documentation](https://developer.themoviedb.org/docs)
- *הבהרת זכויות*: מוצר זה משתמש ב-API של TMDb אך אינו מאושר או מאומת רשמית על ידי TMDb.

---

## יכולות מרכזיות

1. **שיוך מגדרי דטרמיניסטי**: המרת קוד מגדר ב-TMDb לכינויי גוף תקניים (`את/היא` מול `אתה/הוא`), המונעת שגיאות פנייה ישירה בעברית.
2. **איתור שחקני אורח**: פענוח דמויות אורחות ספציפיות לכל פרק.
3. **הכנת הקשר עלילתי**: הזרקת תקציר הפרק והז'אנר לתוך פרומפט התרגום.
4. **הנחיות דיאלקט**: זיהוי אנגלית בריטית מול אמריקאית ומניעת שגיאות סלנג ותרגום מילולי.

---

## הגדרת מפתח גישה

```bash
export TMDB_API_KEY="your_api_key_or_bearer_token"
```

אם המשתנה אינו מוגדר, RightSub ממשיכה לפעול בצורה מקומית חלקה (Graceful Fallback).

---

## פקודות שימוש מהירות

### 1. בדיקת מטא-דאטה ישירות מקובץ
```bash
python3 scripts/tmdb_client.py "Boston.Legal.S01E05.1080p.mkv"
```

### 2. הפקת Translation Bible מועשר ב-TMDb
```bash
./rightsub bible "Boston Legal S01E05.en.srt" --tmdb
```

### 3. בניית פרומפטים מונחי הקשר ודיאלקט
```bash
./rightsub prompt-gen "Boston Legal S01E05.en.srt" -b translation_bible.json
```

</div>
