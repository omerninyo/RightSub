/**
 * app.js — RightSub v1.5.0 Interactive Web UI Controller
 * ------------------------------------------------------
 * Powers:
 * 1. Instant Client-Side `.srt` Drag & Drop Mastering (single file, batch, or HE+EN bilingual pair).
 * 2. Interactive "Try Broken Sample Subtitle" button showcasing CP1255/Subabi/Homoglyph/Ad/Number repair.
 * 3. Plex / Infuse / Apple TV Before & After Visual Screen Simulator.
 * 4. Platform Installation Tabs & 1-Click Clipboard Copy.
 * 5. Bilingual RTL (Hebrew) <-> LTR (English) UI Switcher.
 * 6. Live Health Probe when served by `rightsub serve` (`GET /health`).
 */
(function () {
  "use strict";

  const I18N = {
    he: {
      dir: "rtl",
      toggleLabel: "English",
      skip_link: "דלג לתוכן הראשי",
      nav_fixer: "תיקון מיידי בדפדפן",
      nav_showcase: "הדגמת מסך Plex",
      nav_install: "התקנה ואשפים",
      nav_matrix: "0 טוקנים מול AI",
      hero_eyebrow: "תקן UAX #9 Rule N1 · הגנת טורנט Seed-Safe · שרת MCP מובנה",
      hero_title: "כתוביות עברית מושלמות ב-Plex, Infuse ו-Apple TV — בשנייה אחת.",
      hero_lead:
        'סימני שאלה ונקודות קופצים לימין? ג׳יבריש בכתוביות ישנות (Windows-1255)? מספרים הפוכים מ-Subabi? גררו קובץ <code>.srt</code> לתיבה ממול לתיקון מיידי בדפדפן (100% מקומי על המחשב שלכם, 0 העלאה לשרת) — או התקינו את חבילת ה-CLI ושרת ה-MCP לאוטומציה מלאה.',
      hero_cta_install: "⚡ התקנת חבילה מלאה (CLI + MCP)",
      hero_cta_demo: "🧪 נסה על כתובית שבורה לדוגמה",
      trust_1:
        "🔒 <strong>100% פרטיות בדפדפן:</strong> הקובץ מעובד בזיכרון המקומי בלבד ולעולם אינו מועלה לשום שרת.",
      trust_2:
        "🛡️ <strong>Seed-Safe לטורנטים:</strong> מפיק קובץ <code>.he.srt</code> תקני ומשאיר את קובץ המקור ללא נגיעה.",
      trust_3:
        "🤖 <strong>אפס צורך ב-AI לתיקון טכני:</strong> 99% מהכתוביות הקיימות מתוקנות ב-100% דטרמיניזם וב-0 טוקנים.",
      drop_title: "🛠️ מתקן כתוביות מיידי בדפדפן (SubRefine Engine)",
      drop_badge: "100% Client-Side JS",
      drop_prompt: "גררו לכאן קובץ <code>.srt</code> בעברית (או לחצו לבחירה)",
      drop_subprompt:
        "טיפ: ניתן לגרור מספר קובצי <code>.srt</code> יחד, או לגרור זוג <code>Movie.srt</code> + <code>Movie.en.srt</code> להצלבת מספרים הפוכים (<code>84</code> ← <code>48</code>)!",
      opt_clean_ads: "נקה פרסומות וקרדיטים (Torec, Wizdom, טלגרם)",
      opt_clean_speakers: "הסר תוויות דוברים בראש שורה (אלן:, שופט:)",
      diff_heading: "🔍 השוואת שורות שתוקנו בקובץ (לפני ← אחרי):",
      diff_col_before: "לפני (שבור בפלקס / Subabi)",
      diff_col_after: "אחרי (RightSub + RLM)",
      showcase_title: "📺 סימולטור מסך Plex / Infuse / Apple TV",
      showcase_subtitle:
        "ראו כיצד נגנים מודרניים מציגים כתוביות עברית ללא תווי כיווניות או לאחר היפוך ויזואלי ישן, לעומת תוצאת המאסטרינג של RightSub:",
      scen_punct: "1. סימני שאלה ופיסוק קופצים לימין",
      scen_subabi: "2. היפוך Subabi + מספר דו-ספרתי הפוך (84 ← 48)",
      scen_english: "3. מילה באנגלית בסוף משפט (FBI.)",
      scen_cp1255: "4. ג׳יבריש Windows-1255 והומוגליפים (דეייט)",
      tv_before_label: "❌ לפני RightSub (תצוגה שבורה בנגן)",
      tv_after_label: "✔️ אחרי RightSub (תקן UAX #9 Rule N1)",
      install_title: "🚀 התקנה בפקודה אחת: אשף אינטראקטיבי, שרת MCP ואוטומציה",
      install_subtitle:
        "צריכים לטפל בקובצי וידאו שלמים (<code>.mkv</code> / <code>.mp4</code>), עונות שלמות, או לחבר את סוכן ה-AI ושרת המדיה שלכם? בחרו את סביבת העבודה שלכם:",
      mac_step1_title: "1. התקנה גלובלית (Homebrew או סקריפט מהיר)",
      mac_step1_note:
        'או בהתקנה ישירה מ-GitHub: <code>git clone https://github.com/omerninyo/RightSub.git &amp;&amp; cd RightSub &amp;&amp; ./install.sh</code>',
      mac_step2_title: "2. הפעלת האשף האינטראקטיבי ואשף ההקמה (ללא דגלים!)",
      win_step1_title: "1. מתקין אוטומטי לחלונות (מוסיף ל-PATH של המשתמש אוטומטית)",
      win_step1_note:
        "<code>install.bat</code> בודק Python ו-FFmpeg, מתקין תלויות ורושם את <code>rightsub</code> ב-PATH של המשתמש ללא צורך בהרשאות Administrator.",
      win_step2_title: "2. הפעלה מכל חלון CMD או PowerShell",
      mcp_step1_title: "1. רישום אוטומטי לכל סוכני ה-AI בפקודה אחת",
      mcp_step1_note:
        "מזהה ורושם אוטומטית את שרת ה-MCP המקומי (8 כלים) ב-<strong>Google Antigravity</strong>, <strong>Claude Desktop</strong>, <strong>Cursor</strong>, <strong>Windsurf</strong> ו-<strong>Claude Code</strong>.",
      mcp_step2_title: "2. דברו עם הסוכן שלכם בשפה טבעית",
      arr_step1_title: "1. מחולל Hooks ושירותי רקע אוטומטי",
      arr_step1_note:
        "מייצר סקריפטים מוכנים ל-qBittorrent ול-Transmission ב-<code>~/.config/rightsub/hooks/</code>, רושם Webhook חי ב-Sonarr/Radarr, ומתקין שירות רקע.",
      arr_step2_title: "2. שרת Webhook לקונטיינרים ו-NAS (Port 8775)",
      copy_btn: "העתק",
      copied_btn: "הועתק ✓",
      matrix_title: "⚖️ הפרדה הנדסית: תיקון טכני ב-0 טוקנים מול תרגום וליטוש AI",
      matrix_subtitle:
        "99% מהכתוביות הקיימות בעברית אינן דורשות מפתח AI כלל. מודל שפה מופעל אך ורק בתרגום מאפס או בהגהה סמנטית של תרגומים ישנים:",
      mat_col_task: "תרחיש שימוש",
      mat_col_cmd: "כלי / פקודה",
      mat_col_ai: "דורש מפתח AI?",
      mat_col_cost: "עלות טוקנים",
      mat_row1_task:
        "תיקון BiDi ופיסוק לפלקס, ביטול 18 תבניות היפוך Subabi, המרת CP1255, ניקוי פרסומות והומוגליפים",
      mat_row2_task:
        "אימות והיפוך מספרים דו-לשוני (<code>84</code> ← <code>48</code>) ותיקון מונחי קאנון",
      mat_row3_task:
        "בקרת איכות (QA), תאימות זמנים 1:1, גילוי Cue Drift וזיהוי פניות מגדר",
      mat_row4_task:
        "ליטוש סמנטי של תרגום ישן/חובבני עם סקירה אינטראקטיבית שורה-אחר-שורה",
      mat_row5_task:
        "תרגום סרט או סדרה חדשים מאנגלית לעברית מאפס (כולל TMDb ו-Translation Bible)",
      no_ai: "❌ לא (100% דטרמיניסטי)",
      opt_ai: "✔️ אופציונלי (למקרי קצה נדירים)",
      req_ai: "✔️ כן (או דרך סוכן ה-MCP)",
      footer_copy:
        "<strong>RightSub v1.5.0</strong> · קוד פתוח ברישיון MIT · 189 בדיקות אוטומטיות · עיבוד מקומי ב-100% ללא העלאת קבצים.",
      stat_cues: "כתוביות נסרקו",
      stat_fixed: "שורות תוקנו",
      stat_ads: "פרסומות הוסרו",
      stat_nums: "מספרים הופכו חזרה",
      download_btn: "⬇️ הורד קובץ מתוקן",
      video_warn:
        "זהו קובץ וידאו. לחילוץ ותרגום של קובצי MKV/MP4 על הדיסק המקומי, הריצו בטרמינל: rightsub auto",
    },
    en: {
      dir: "ltr",
      toggleLabel: "עברית",
      skip_link: "Skip to main content",
      nav_fixer: "Instant Browser Fixer",
      nav_showcase: "Plex TV Simulator",
      nav_install: "Install & Wizards",
      nav_matrix: "0-Token vs. AI Matrix",
      hero_eyebrow: "Unicode UAX #9 Rule N1 · Seed-Safe Torrents · Native MCP Server",
      hero_title: "Flawless Hebrew Subtitles on Plex, Infuse & Apple TV — in 1 Second.",
      hero_lead:
        'Jumping question marks and periods? Legacy Windows-1255 gibberish? Reversed Subabi numbers? Drag & drop any <code>.srt</code> file into the box to master it instantly in your browser (100% local in memory, 0 server uploads) — or install the full CLI & MCP Server.',
      hero_cta_install: "⚡ Install Full Suite (CLI + MCP)",
      hero_cta_demo: "🧪 Try on a Broken Sample Subtitle",
      trust_1:
        "🔒 <strong>100% Browser Privacy:</strong> Files are processed strictly in local memory and never uploaded anywhere.",
      trust_2:
        "🛡️ <strong>Seed-Safe for Torrents:</strong> Outputs a clean <code>.he.srt</code> copy while keeping source torrents untouched.",
      trust_3:
        "🤖 <strong>Zero AI Needed for Technical Repairs:</strong> 99% of existing subtitles are fixed deterministically at 0 token cost.",
      drop_title: "🛠️ Instant Browser Subtitle Master (SubRefine Engine)",
      drop_badge: "100% Client-Side JS",
      drop_prompt: "Drag & drop Hebrew <code>.srt</code> file(s) here (or click to browse)",
      drop_subprompt:
        "Tip: Drop multiple <code>.srt</code> files at once, or drop a pair of <code>Movie.srt</code> + <code>Movie.en.srt</code> to un-flip reversed 2-digit numbers (<code>84</code> → <code>48</code>)!",
      opt_clean_ads: "Strip translator credit banners & ads (Torec, Wizdom, Telegram)",
      opt_clean_speakers: "Strip leading speaker labels (Alan:, Judge:)",
      diff_heading: "🔍 Repaired Lines Inspector (Before → After):",
      diff_col_before: "Before (Broken in Plex / Subabi)",
      diff_col_after: "After (RightSub + UAX #9 RLM)",
      showcase_title: "📺 Interactive Plex / Infuse / Apple TV Screen Simulator",
      showcase_subtitle:
        "Compare how modern media players render unmastered or visually pre-flipped Hebrew subtitles versus RightSub's UAX #9 Rule N1 output:",
      scen_punct: "1. Reversed Trailing Question Marks & Punctuation",
      scen_subabi: "2. Subabi Visual Flip + Reversed Number (84 → 48)",
      scen_english: "3. Sentence Ending with English Word (FBI.)",
      scen_cp1255: "4. Windows-1255 Gibberish & Homoglyphs (דეייט)",
      tv_before_label: "❌ Before RightSub (Broken Player Rendering)",
      tv_after_label: "✔️ After RightSub (UAX #9 Rule N1 Mastered)",
      install_title: "🚀 One-Command Install: Interactive Wizard, MCP Server & Automation",
      install_subtitle:
        "Need to process full video containers (<code>.mkv</code> / <code>.mp4</code>), entire TV seasons, or connect your AI agent and media stack? Select your platform:",
      mac_step1_title: "1. Global Install (Homebrew Tap or Fast Script)",
      mac_step1_note:
        "Or install from GitHub: <code>git clone https://github.com/omerninyo/RightSub.git &amp;&amp; cd RightSub &amp;&amp; ./install.sh</code>",
      mac_step2_title: "2. Launch Interactive Mastering & Setup Wizards (Zero Flags!)",
      win_step1_title: "1. Automated Windows Installer (Auto-Registers User PATH)",
      win_step1_note:
        "<code>install.bat</code> checks Python & FFmpeg, installs dependencies, and registers <code>rightsub</code> in your Windows User PATH automatically.",
      win_step2_title: "2. Run from Any CMD or PowerShell Window",
      mcp_step1_title: "1. One-Command Multi-Agent MCP Installer",
      mcp_step1_note:
        "Automatically detects and registers RightSub's local MCP Server (8 tools) in <strong>Google Antigravity</strong>, <strong>Claude Desktop</strong>, <strong>Cursor</strong>, <strong>Windsurf</strong>, and <strong>Claude Code</strong>.",
      mcp_step2_title: "2. Control RightSub via Natural Language",
      arr_step1_title: "1. Automated Downloader Hooks & Background Service",
      arr_step1_note:
        "Generates ready-to-use qBittorrent & Transmission hooks in <code>~/.config/rightsub/hooks/</code>, registers Sonarr/Radarr webhooks, and installs OS background services.",
      arr_step2_title: "2. Container & NAS Webhook Daemon (Port 8775)",
      copy_btn: "Copy",
      copied_btn: "Copied ✓",
      matrix_title: "⚖️ Architectural Separation: 0-Token Technical Repair vs. AI Translation",
      matrix_subtitle:
        "99% of existing Hebrew subtitles require zero AI keys. LLMs are invoked strictly for translating from scratch or polishing rare legacy drafts:",
      mat_col_task: "Workflow / Operation",
      mat_col_cmd: "Tool / Command",
      mat_col_ai: "Requires AI Key?",
      mat_col_cost: "Token Cost",
      mat_row1_task:
        "Plex BiDi RLM wrapping, 18-pattern Subabi un-flipping, CP1255 recovery, ad & homoglyph cleaning",
      mat_row2_task:
        "Bilingual 2-digit number un-flipping (<code>84</code> → <code>48</code>) & deterministic canon pass",
      mat_row3_task:
        "Red Team QA audit, 1:1 cue parity, Cue Drift & vocative/morphological gender verification",
      mat_row4_task:
        "Semantic AI proofreading of old/amateur drafts with interactive line-by-line diff review",
      mat_row5_task:
        "Full English-to-Hebrew subtitle translation from scratch (with TMDb & Translation Bible)",
      no_ai: "❌ No (100% Deterministic)",
      opt_ai: "✔️ Optional (Rare Edge Cases)",
      req_ai: "✔️ Yes (or via MCP Agent)",
      footer_copy:
        "<strong>RightSub v1.5.0</strong> · MIT Open Source · 189 Automated Tests · 100% Local Processing.",
      stat_cues: "Cues Scanned",
      stat_fixed: "Lines Repaired",
      stat_ads: "Ads Stripped",
      stat_nums: "Numbers Un-Flipped",
      download_btn: "⬇️ Download Mastered .he.srt",
      video_warn:
        "Video container detected. To extract and master MKV/MP4 files on disk, run locally: rightsub auto",
    },
  };

  const SCENARIOS = {
    punct: {
      before1: "?אלן, אתה באמת חושב שהשופט יקבל את זה",
      before2: "!אין לנו שום סיכוי בלי ראיות-",
      after1: "\u200Fאלן, אתה באמת חושב שהשופט יקבל את זה?\u200F",
      after2: "\u200F- אין לנו שום סיכוי בלי ראיות!\u200F",
      expBeforeHe:
        "ללא תו RLM סמוי אחרי סימן הפיסוק, אלגוריתם ה-BiDi של Plex מפרש את סימן השאלה כתו ניטרלי בראש שורת LTR ומקפיץ אותו לימין.",
      expAfterHe:
        "עטיפת השורה ב-RLM מוביל ו-RLM סוגר (אחרי סימן השאלה) נועלת את הפיסוק והמקף במקומם הטבעי בכל נגן.",
      expBeforeEn:
        "Without a trailing RLM after neutral punctuation, Plex's LTR paragraph renderer places '?' and '!' on the visual right edge.",
      expAfterEn:
        "Sandwiching the line between leading and trailing RLM marks (UAX #9 Rule N1) locks punctuation to the visual left.",
    },
    subabi: {
      before1: ".84 שעות חיכינו לעד המפתח הזה-",
      before2: ")חדר הישיבות הראשי(",
      after1: "\u200F- 48 שעות חיכינו לעד המפתח הזה.\u200F",
      after2: "\u200F(חדר הישיבות הראשי)\u200F",
      expBeforeHe:
        "תוכנות ישנות (Subabi) הפכו פיזית את הנקודה, המקף, הסוגריים ואפילו את המספר '48' ל-'84' בתוך הקובץ.",
      expAfterHe:
        "RightSub מזהה קוטביות הפוכה, משחזר את כל 18 תבניות ה-Subabi והסוגריים, ומצליב מול האנגלית כדי לתקן את 84 חזרה ל-48!",
      expBeforeEn:
        "Legacy visual flippers (Subabi) physically moved periods, dashes, parentheses, and reversed '48' into '84'.",
      expAfterEn:
        "RightSub reverses all 18 visual-flip patterns, restores parentheses, and cross-checks English cues to un-flip 84 -> 48.",
    },
    english: {
      before1: ".ראיתי את הסוכנים של ה-FBI",
      before2: '!זה תיק פדרלי של ה-CIA',
      after1: "\u200Fראיתי את הסוכנים של ה-FBI\u200F.\u200F",
      after2: "\u200Fזה תיק פדרלי של ה-CIA\u200F!\u200F",
      expBeforeHe:
        "כאשר משפט עברי מסתיים במילה באנגלית (FBI), הנקודה נצמדת לימין המילה האנגלית או קופצת לתחילת השורה.",
      expAfterHe:
        "RightSub מזריק תו RLM ייעודי בין האות הלטינית האחרונה לבין הנקודה (FBI\\u200F.\\u200F), כך שהנקודה ננעלת בשמאל המשפט.",
      expBeforeEn:
        "When a Hebrew sentence ends with an LTR word (FBI), trailing punctuation attaches to the right side of the English word.",
      expAfterEn:
        "RightSub injects an inner RLM immediately before trailing punctuation after Latin words (FBI\\u200F.\\u200F).",
    },
    cp1255: {
      before1: "àðé øåöä לצאת ל-ד\u10D4ייט הערב.",
      before2: 'סונכרן על ידי צוות טורק - Torec.net',
      after1: "\u200Fאני רוצה לצאת ל-דייט הערב.\u200F",
      after2: "\u200F[שורת פרסומת וקרדיט הוסרה אוטומטית]\u200F",
      expBeforeHe:
        "קידוד Windows-1255 מופיע כג׳יבריש, התו הגאורגי 'ე' שתול בתוך המילה 'דეייט', ושורות פרסומת קוטעות את הצפייה.",
      expAfterHe:
        "פענוח אוטומטי מ-CP1255 ל-UTF-8 נקי, המרת הומוגליפים מ-7 מערכות כתב לעברית תקנית ('דייט'), וניקוי פרסומות.",
      expBeforeEn:
        "Windows-1255 bytes render as mojibake gibberish, Georgian homoglyph 'ე' corrupts 'דייט', and ad banners clutter playback.",
      expAfterEn:
        "Auto-converts CP1255 to UTF-8, normalizes 7 foreign homoglyph scripts into pure Hebrew, and strips ad banners.",
    },
  };

  const DEMO_HE_SRT = [
    "1",
    "00:00:01,000 --> 00:00:03,500",
    "<i>סונכרן על ידי צוות טורק - Torec.net",
    "אריאל אפרתי</i>",
    "",
    "2",
    "00:00:04,100 --> 00:00:07,200",
    ".שלום אלן, חיכינו לך 84 שעות במשרד-",
    "",
    "3",
    "00:00:07,800 --> 00:00:11,000",
    "?יצאת ל-ד\u10D4ייט עם סוכנת של ה-FBI",
    "",
    "4",
    "00:00:11,500 --> 00:00:14,400",
    ')בית המשפט העליון של ארה"ב(',
    "",
  ].join("\n");

  const DEMO_EN_SRT = [
    "1",
    "00:00:01,000 --> 00:00:03,500",
    "Previously on Boston Legal...",
    "",
    "2",
    "00:00:04,100 --> 00:00:07,200",
    "- Hello Alan, we waited 48 hours for you at the office.",
    "",
    "3",
    "00:00:07,800 --> 00:00:11,000",
    "Did you go on a date with an FBI agent?",
    "",
    "4",
    "00:00:11,500 --> 00:00:14,400",
    "(The Supreme Court of the USA)",
    "",
  ].join("\n");

  let currentLang = localStorage.getItem("rightsub_lang") || "he";
  let currentScenario = "punct";

  function applyLanguage(lang) {
    currentLang = lang in I18N ? lang : "he";
    localStorage.setItem("rightsub_lang", currentLang);
    const dict = I18N[currentLang];

    document.documentElement.lang = currentLang;
    document.documentElement.dir = dict.dir;

    const toggleLabel = document.getElementById("lang-toggle-label");
    if (toggleLabel) toggleLabel.textContent = dict.toggleLabel;

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });

    renderScenario(currentScenario);
  }

  function renderScenario(key) {
    currentScenario = key in SCENARIOS ? key : "punct";
    const sc = SCENARIOS[currentScenario];
    const b1 = document.getElementById("tv-before-line1");
    const b2 = document.getElementById("tv-before-line2");
    const a1 = document.getElementById("tv-after-line1");
    const a2 = document.getElementById("tv-after-line2");
    const expB = document.getElementById("tv-before-explain");
    const expA = document.getElementById("tv-after-explain");

    if (b1) b1.textContent = sc.before1;
    if (b2) b2.textContent = sc.before2;
    if (a1) a1.textContent = sc.after1;
    if (a2) a2.textContent = sc.after2;
    if (expB) expB.textContent = currentLang === "he" ? sc.expBeforeHe : sc.expBeforeEn;
    if (expA) expA.textContent = currentLang === "he" ? sc.expAfterHe : sc.expAfterEn;
  }

  function renderResults(processedFiles) {
    const dict = I18N[currentLang];
    const resultsContainer = document.getElementById("fixer-results");
    const statsGrid = document.getElementById("stats-grid");
    const downloadsList = document.getElementById("downloads-list");
    const diffWrapper = document.getElementById("diff-preview-wrapper");
    const diffTbody = document.getElementById("diff-tbody");

    if (!resultsContainer || !statsGrid || !downloadsList) return;

    let totalSubs = 0;
    let totalFixed = 0;
    let totalAds = 0;
    let totalNums = 0;
    const allDiffs = [];

    downloadsList.innerHTML = "";

    for (const item of processedFiles) {
      if (item.error) {
        const errDiv = document.createElement("div");
        errDiv.className = "download-item";
        errDiv.innerHTML = `<div class="download-meta"><span class="download-filename">${escapeHtml(
          item.name
        )}</span><span class="download-submeta" style="color:#fca5a5">${escapeHtml(
          item.error
        )}</span></div>`;
        downloadsList.appendChild(errDiv);
        continue;
      }

      totalSubs += item.stats.totalSubs;
      totalFixed += item.stats.modifiedLines;
      totalAds += item.stats.adsRemoved;
      totalNums += item.stats.numbersUnflipped;

      for (const d of item.stats.sampleDiffs) {
        if (allDiffs.length < 20 && d.visualChange) {
          allDiffs.push(d);
        }
      }

      const blob = new Blob([item.stats.resultText], {
        type: "text/plain;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);

      const row = document.createElement("div");
      row.className = "download-item";
      row.innerHTML = `
        <div class="download-meta">
          <span class="download-filename">${escapeHtml(item.outName)}</span>
          <span class="download-submeta">
            ${escapeHtml(item.encoding.toUpperCase())} → UTF-8 ·
            ${item.stats.isPreflippedFile ? "Subabi Un-Flipped · " : ""}
            ${item.stats.modifiedLines} lines mastered
          </span>
        </div>
        <a href="${url}" download="${escapeHtml(
        item.outName
      )}" class="btn btn-primary">${dict.download_btn}</a>
      `;
      downloadsList.appendChild(row);
    }

    statsGrid.innerHTML = `
      <div class="stat-box">
        <div class="stat-value">${totalSubs}</div>
        <div class="stat-label">${dict.stat_cues}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalFixed}</div>
        <div class="stat-label">${dict.stat_fixed}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalAds}</div>
        <div class="stat-label">${dict.stat_ads}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalNums}</div>
        <div class="stat-label">${dict.stat_nums}</div>
      </div>
    `;

    if (allDiffs.length > 0 && diffWrapper && diffTbody) {
      diffTbody.innerHTML = allDiffs
        .map(
          (d) => `
        <tr>
          <td dir="ltr">#${d.cue}</td>
          <td class="diff-before" dir="ltr">${escapeHtml(d.before)}</td>
          <td class="diff-after" dir="rtl">${escapeHtml(d.after)}</td>
        </tr>
      `
        )
        .join("");
      diffWrapper.hidden = false;
    } else if (diffWrapper) {
      diffWrapper.hidden = true;
    }

    resultsContainer.hidden = false;
  }

  async function handleFiles(fileList) {
    if (!fileList || fileList.length === 0 || !window.RightSubRefine) return;
    const dict = I18N[currentLang];
    const cleanAds = document.getElementById("opt-clean-ads")?.checked ?? true;
    const cleanSpeakers =
      document.getElementById("opt-clean-speakers")?.checked ?? false;

    const decodedFiles = [];
    for (const file of Array.from(fileList)) {
      const lower = file.name.toLowerCase();
      if (/\.(mkv|mp4|avi|mov|m4v)$/.test(lower)) {
        decodedFiles.push({
          name: file.name,
          error: `${dict.video_warn} "${file.name}"`,
        });
        continue;
      }
      const buffer = await file.arrayBuffer();
      const { text, encoding } = window.RightSubRefine.decodeSrtBuffer(buffer);
      const hebCheck = window.RightSubRefine.detectHebrew(text);
      decodedFiles.push({
        name: file.name,
        text,
        encoding,
        isHebrew: hebCheck.isHebrew,
      });
    }

    // Pair English companion SRT if user dropped both HE and EN files
    const enCandidate = decodedFiles.find((f) => !f.error && !f.isHebrew);
    const enContent = enCandidate ? enCandidate.text : null;

    const processed = [];
    for (const f of decodedFiles) {
      if (f.error) {
        processed.push(f);
        continue;
      }
      if (!f.isHebrew && decodedFiles.some((other) => other.isHebrew)) {
        // Used as English companion reference for bilingual number un-flipping
        continue;
      }
      if (!f.isHebrew) {
        processed.push({
          name: f.name,
          error:
            currentLang === "he"
              ? "קובץ זה זוהה ככתובית באנגלית/שפה זרה (מוגן משינוי)."
              : "Foreign/English subtitle detected (protected from modification).",
        });
        continue;
      }

      const stats = window.RightSubRefine.processSrtContent(f.text, {
        cleanAds,
        cleanSpeakers,
        enContent,
      });
      const outName = window.RightSubRefine.getSeedSafeFilename(f.name);
      processed.push({
        name: f.name,
        outName,
        encoding: f.encoding,
        stats,
      });
    }

    renderResults(processed);
  }

  function runDemoSample() {
    if (!window.RightSubRefine) return;
    const cleanAds = document.getElementById("opt-clean-ads")?.checked ?? true;
    const cleanSpeakers =
      document.getElementById("opt-clean-speakers")?.checked ?? false;

    const stats = window.RightSubRefine.processSrtContent(DEMO_HE_SRT, {
      cleanAds,
      cleanSpeakers,
      enContent: DEMO_EN_SRT,
    });
    renderResults([
      {
        name: "Boston.Legal.S01E01.srt",
        outName: "Boston.Legal.S01E01.he.srt",
        encoding: "windows-1255 + subabi",
        stats,
      },
    ]);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function checkLocalDaemonHealth() {
    try {
      const resp = await fetch("/health", { cache: "no-store" });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data && data.status === "healthy") {
        const badge = document.getElementById("daemon-status-badge");
        const text = document.getElementById("daemon-status-text");
        if (badge && text) {
          const count = data.metrics?.processed_count ?? 0;
          text.textContent = `Daemon v${data.version} Active (${count} mastered)`;
          badge.hidden = false;
        }
      }
    } catch (_) {
      // Static hosting (GitHub Pages) — no local daemon running
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyLanguage(currentLang);
    checkLocalDaemonHealth();

    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        applyLanguage(currentLang === "he" ? "en" : "he");
      });
    }

    const demoBtn = document.getElementById("load-demo-btn");
    if (demoBtn) {
      demoBtn.addEventListener("click", runDemoSample);
    }

    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          fileInput.click();
        }
      });
      fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
      dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
      });
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer?.files?.length) {
          handleFiles(e.dataTransfer.files);
        }
      });
    }

    // TV Scenario buttons
    document.querySelectorAll(".scenario-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        document
          .querySelectorAll(".scenario-btn")
          .forEach((b) => b.classList.remove("active"));
        this.classList.add("active");
        renderScenario(this.getAttribute("data-scenario"));
      });
    });

    // Installation Tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const target = this.getAttribute("data-tab");
        document.querySelectorAll(".tab-btn").forEach((b) => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        this.classList.add("active");
        this.setAttribute("aria-selected", "true");

        document.querySelectorAll(".tab-panel").forEach((panel) => {
          if (panel.id === `tab-${target}`) {
            panel.hidden = false;
            panel.classList.add("active");
          } else {
            panel.hidden = true;
            panel.classList.remove("active");
          }
        });
      });
    });

    // Copy buttons
    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", async function () {
        const targetId = this.getAttribute("data-copy-target");
        const codeEl = document.getElementById(targetId);
        if (!codeEl) return;
        try {
          await navigator.clipboard.writeText(codeEl.textContent.trim());
          const dict = I18N[currentLang];
          this.textContent = dict.copied_btn;
          setTimeout(() => {
            this.textContent = I18N[currentLang].copy_btn;
          }, 1800);
        } catch (_) {}
      });
    });
  });
})();
