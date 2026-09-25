<div dir="rtl">

# 📦 מדריך התקנה גלובלית והפצה — RightSub

<p align="right">
  <b>שפה / Language:</b>
  <b>עברית</b> |
  <a href="INSTALLATION_GUIDE.md"><b>English</b></a>
</p>

מדריך זה מסביר כיצד להתקין את **RightSub** כפקודת מערכת גלובלית ב-macOS וב-Linux, כך שתוכלו להקליד `rightsub` ישירות מכל חלון טרמינל ובכל תיקייה, בדיוק כמו כלים המותקנים דרך Homebrew.

---

## 🧭 השוואת שיטות ההתקנה

| שיטה | פקודת ההתקנה | מתי להשתמש? | דרישות |
| :--- | :--- | :--- | :---: |
| **1. סקריפט התקנה מהיר (`install.sh`)** | `./install.sh` | **הכי מומלץ למחשב האישי שלך עכשיו** (ללא צורך ב-sudo) | Python 3 |
| **2. התקנת Homebrew Tap (`brew`)** | `brew install omerninyo/tap/rightsub` | **הכי מקצועי לחלוקה עם משתמשים אחרים** (כמו כלי brew רשמי) | Homebrew |
| **3. התקנת Python מבודדת (`pipx`)** | `pipx install .` | מומלץ למפתחי Python שרוצים בידוד סביבות מלא | pipx |
| **4. קיצור ידני ב-Shell (`alias`)** | `alias rightsub="..."` | פתרון זמני ללא יצירת קבצים | Zsh / Bash |

---

## ⚡ שיטה 1: סקריפט ההתקנה המהיר (`install.sh`) — מומלץ!

סקריפט ההתקנה [install.sh](file:///Volumes/Other/Antigravity/RightSub/install.sh) בודק את קיום התלויות (`python3`, `ffmpeg`), מתקין את הספריות הנדרשות מ-`requirements.txt`, ומייצר קישור הרצה סימבולי גלובלי ב-`~/.local/bin/rightsub`.

### התקנה מקומית מתוך תיקיית המאגר:
```bash
cd /Volumes/Other/Antigravity/RightSub
./install.sh
```

### התקנה מרחוק במחשב חדש בפקודה אחת:
```bash
curl -fsSL https://raw.githubusercontent.com/omerninyo/RightSub/main/install.sh | bash
```

### בדיקת ההתקנה:
פתחו חלון טרמינל חדש בכל מקום והקלידו:
```bash
rightsub --help
```

### הסרת ההתקנה (Uninstall):
```bash
./install.sh --uninstall
```

---

## 🍺 שיטה 2: חבילת Homebrew Tap רשמית (`brew install`)

רוצים שכל משתמש Mac בעולם יוכל להתקין את RightSub בפקודה אחת של `brew`?  
לשם כך נוצר הקובץ [Formula/rightsub.rb](file:///Volumes/Other/Antigravity/RightSub/Formula/rightsub.rb).

### צעדי הקמת ה-Tap ב-GitHub (חד-פעמי):

1. **פתיחת מאגר Tap ב-GitHub:**  
   היכנסו ל-GitHub ופתחו מאגר ציבורי חדש בשם:  
   `homebrew-tap` (תחת חשבון המשתמש שלכם, למשל `https://github.com/omerninyo/homebrew-tap`).
   > *הערה: Homebrew מזהה אוטומטית מאגרים ששמם מתחיל ב-`homebrew-` כ-Taps רשמיים.*

2. **העתקת נוסחת ההתקנה:**  
   במאגר ה-Tap החדש, צרו תיקייה בשם `Formula` והעתיקו אליה את הקובץ:  
   `Formula/rightsub.rb`.

3. **דחיפת השינויים ל-GitHub:**  
   בצעו Commit ו-Push למאגר ה-Tap.

### מעכשיו – איך מתקינים דרך Homebrew?
כל משתמש יכול כעת להקליד בטרמינל שלו:
```bash
brew tap omerninyo/tap
brew install rightsub
```
או בפקודה אחת קצרה:
```bash
brew install omerninyo/tap/rightsub
```

Homebrew ידאג להתקין אוטומטית את `ffmpeg` ואת `python`, ייצור סביבה וירטואלית פרטית בתוך `/opt/homebrew/Cellar/rightsub/`, ויקשר את הפקודה `rightsub` ישירות ל-`/opt/homebrew/bin/rightsub`.

---

## 🐍 שיטה 3: התקנה מבודדת באמצעות `pipx`

ב-macOS מודרני מומלץ שלא להתקין חבילות CLI ישירות ל-Python הגלובלי כדי לא להתנגש עם חבילות מערכת. כלי ה-CLI המומלץ לכך הוא `pipx`:

```bash
# אם pipx עדיין לא מותקן:
brew install pipx
pipx ensurepath

# התקנת RightSub ישירות מהתיקייה המקומית:
cd /Volumes/Other/Antigravity/RightSub
pipx install .

# או התקנה ישירות ממאגר ה-GitHub:
pipx install git+https://github.com/omerninyo/RightSub.git
```

---

## ⚙️ פתרון תקלות בנתיבי המערכת (PATH Troubleshooting)

אם הרצתם את `./install.sh` וקיבלתם שגיאה שהפקודה `rightsub` אינה מזוהה, ודאו שספריית `~/.local/bin` מופיעה ב-`PATH` שלכם:

1. פתחו את קובץ הגדרות ה-Shell שלכם:
   ```bash
   nano ~/.zshrc
   ```
2. הוסיפו בסוף הקובץ את השורה:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. שמרו וטענו את ההגדרות מחדש:
   ```bash
   source ~/.zshrc
   ```

</div>
