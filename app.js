/**
 * app.js — RightSub v1.5.0 Interactive Web UI & Live Sandbox Controller
 * ----------------------------------------------------------------------
 * Powers:
 * 1. Instant Client-Side `.srt` Drag & Drop Mastering (single file, batch, or HE+EN bilingual pair).
 * 2. Live Single-Line & Multi-Line Subtitle Sandbox (works effortlessly on mobile & desktop).
 * 3. Plex / Infuse / Apple TV Before & After Visual Screen Simulator.
 * 4. Platform Installation Tabs, WAI-ARIA Roving Tablist Keyboard Navigation & 1-Click Clipboard Copy.
 * 5. Complete Bilingual RTL (Hebrew) <-> LTR (English) & Flat Light/Dark Theme Switcher.
 * 6. Live Health Probe when served by `rightsub serve` (`GET /health`).
 */
(function () {
  "use strict";

  const I18N = {
    he: {
      dir: "rtl",
      toggleLabel: "EN",
      page_title: "RightSub — מאסטרינג, תיקון כיווניות ותרגום כתוביות בעברית",
      page_desc:
        "כלי קוד פתוח לתיקון פיסוק וכיווניות (BiDi) בכתוביות עברית עבור Plex, Infuse ו-Apple TV. כולל מנוע תיקון מיידי בדפדפן, אשף CLI, הגנת טורנט (Seed-Safe) ושרת MCP מובנה.",
      aria_home: "דף הבית של RightSub",
      aria_nav: "ניווט ראשי",
      aria_theme: "החלף ערכת נושא (כהה / בהיר)",
      aria_lang: "החלף שפה לאנגלית (Switch to English)",
      aria_gh: "מאגר קוד המקור ב-GitHub",
      aria_workbench: "סביבת התנסות SubRefine",
      aria_wb_tabs: "מצב התנסות",
      aria_scenarios: "בחירת תרחיש תצוגה בנגן",
      aria_platforms: "פלטפורמות התקנה",
      skip_link: "דלג לתוכן הראשי",
      nav_studio: "התנסות חיה",
      nav_capabilities: "יכולות",
      nav_simulator: "סימולטור",
      nav_install: "התקנה ו-CLI",
      nav_architecture: "מתי AI?",
      hero_kicker: "OPEN-SOURCE SUBTITLE ENGINEERING · UAX #9 RULE N1",
      hero_title: "תיקון כיווניות, קידוד ומאסטרינג לכתוביות עברית.",
      hero_lead:
        "RightSub מתקנת את הבעיות שנגני מדיה (Plex, Infuse, Apple TV, LG WebOS) אינם פותרים לבד: סימני שאלה ונקודות שקופצים לימין, כתוביות שעברו היפוך ויזואלי ישן (Subabi), קידוד Windows-1255 שמופיע כג׳יבריש, ומספרים דו-ספרתיים שהתהפכו.",
      pillar1_title: "עיבוד דטרמיניסטי מקומי (0 טוקנים)",
      pillar1_desc:
        "תיקון טכני של כתוביות קיימות רץ ב-100% אלגוריתמיקה מקומית — בדפדפן או בטרמינל — ללא מפתח AI וללא שליחת מידע לשרת.",
      pillar2_title: "הגנת טורנט (Seed-Safe)",
      pillar2_desc:
        "מזהה אוטומטית עברית בתוך כל קובץ <code>.srt</code>, שומר על הקובץ המקורי ללא שינוי בדיסק, ומייצר קובץ <code>.he.srt</code> נפרד.",
      pillar3_title: "CLI, אוטומציה ושרת MCP לסוכני AI",
      pillar3_desc:
        "חבילה מלאה ל-macOS, Windows ו-Docker עם חיבור ל-Sonarr/qBittorrent ותרגום מלא מאנגלית לעברית דרך סוכני AI או Ollama.",
      hero_cta_cli: "התקנת CLI ושרת MCP",
      hero_cta_how: "איך המנוע עובד",
      wb_tab_file: "תיקון קובץ \u2066.srt\u2069",
      wb_tab_sandbox: "בדיקת שורה חיה",
      wb_privacy: "רץ מקומית בדפדפן",
      drop_prompt: "גררו לכאן קובץ <code>.srt</code> או לחצו לבחירה מהמכשיר",
      drop_subprompt:
        "תומך בקובץ בודד, מספר קבצים יחד, או זוג <code>Movie.srt</code> + <code>Movie.en.srt</code> להצלבת מספרים הפוכים (<code>84</code> ← <code>48</code>).",
      opt_clean_ads: "נקה פרסומות וקרדיטים",
      opt_clean_speakers: "הסר תוויות דובר (אלן:)",
      hero_cta_demo: "טען קובץ דוגמה שבור",
      diff_heading: "שורות שתוקנו בקובץ (לפני לעומת אחרי)",
      diff_col_before: "לפני (מקור שבור)",
      diff_col_after: "אחרי (RightSub + UAX #9)",
      sb_preset_label: "דוגמאות מוכנות:",
      sb_chip_1: "פיסוק קופץ",
      sb_chip_2: "היפוך Subabi",
      sb_chip_3: "מילה באנגלית (FBI.)",
      sb_chip_4: "תו זר (דეייט) + ראשי תיבות",
      sb_input_label: "הקלידו או הדביקו שורת כתובית לבדיקה:",
      sb_out_broken: "תצוגה שבורה בנגן (ללא RightSub)",
      sb_out_fixed: "תצוגה מתוקנת בנגן (אחרי RightSub)",
      sb_unicode_label: "מבנה תווים סמויים (Unicode Memory View):",
      cap_kicker: "SYSTEM CAPABILITIES",
      cap_title: "מה RightSub עושה בפועל",
      cap_subtitle:
        "המערכת מפרידה בין שני מנועים עצמאיים: מנוע מאסטרינג דטרמיניסטי לכתוביות קיימות (SubRefine), ומנוע תרגום והגהה מבוסס סוכני AI (SubSwarm).",
      badge_deterministic: "100% דטרמיניסטי · 0 טוקנים",
      badge_seedsafe: "הגנת טורנט פעילה",
      badge_ai: "סוכני AI / Ollama",
      cap1_title: "תיקון כיווניות (BiDi) וביטול היפוכי Subabi",
      cap1_desc:
        'נגנים כמו Plex ו-Apple TV מציגים סימני פיסוק בסוף משפט עברי (<code>?</code>, <code>!</code>, <code>.</code>) בצד ימין של השורה. בנוסף, אלפי כתוביות ישנות ברשת עברו "היפוך ויזואלי" (<code>Subabi</code>) שהפך פיזית את הנקודות והסוגריים בקובץ. RightSub מזהה את קוטביות הקובץ, משחזר 18 תבניות היפוך ישנות, ועוטף כל שורה בתווי <code>RLM</code> (<code>\\u200F</code>) לפי תקן <code>UAX #9 Rule N1</code> של יוניקוד.',
      cap2_title: "הצלת קידוד Windows-1255, הומוגליפים והצלבת מספרים",
      cap2_desc:
        'זיהוי אוטומטי ברמת הבייטים של קובצי <code dir="ltr">CP1255</code> / <code dir="ltr">ISO-8859-8</code> והמרתם ל-<code dir="ltr">UTF-8</code> תקני. ניקוי תווים זרים שהסתננו למילים בעברית מ-7 מערכות כתב (כגון האות הגאורגית ב-<code dir="rtl">\u202Eד\u10D4ייט\u202C</code> ← <code dir="rtl">דייט</code>), הסרת שורות פרסומת וקרדיטים, והיפוך חזרה של מספרים דו-ספרתיים (<code dir="ltr">84</code> ← <code dir="ltr">48</code>) בהצלבה מול כתובית באנגלית.',
      cap3_title: "זיהוי עברית לפי תוכן ושמירת <code>.he.srt</code> נפרד",
      cap3_desc:
        "הורדתם סרט עם קובץ <code>Movie.srt</code> רגיל (ללא סיומת <code>.he.srt</code>) או תיקיית <code>Subs/</code>? RightSub סורקת את תוכן הקובץ, מזהה שמדובר בעברית, משאירה את קובץ ה-<code>.srt</code> המקורי ללא שום שינוי בדיסק כדי לא לשבור שיתוף טורנט ב-qBittorrent/Transmission, ושומרת קובץ <code>Movie.he.srt</code> מתוקן לצד הווידאו.",
      cap4_title: "תרגום מאנגלית לעברית וחיבור MCP לסוכני AI",
      cap4_desc:
        'כאשר אין כתוביות בעברית כלל, RightSub מחלצת כתוביות מובנות מ-<code>.mkv</code>/<code>.mp4</code> (או מתמללת שמע מקומית), בונה מילון דמויות ומגדר מ-TMDb (<code dir="rtl">את/היא</code> מול <code dir="rtl">אתה/הוא</code>), ומתרגמת בהתאמת שורות 1:1 דרך שרת ה-MCP המובנה (Claude, Cursor, Antigravity), Gemini או Ollama מקומי.',
      sim_kicker: "VISUAL COMPARISON",
      showcase_title: "השוואת תצוגה בנגן: לפני לעומת אחרי",
      showcase_subtitle:
        "בחרו תרחיש כדי לראות איך אותה שורת כתובית נראית בנגן הטלוויזיה לפני ואחרי עיבוד ב-RightSub:",
      scen_punct: "01. סימני שאלה ופיסוק קופצים לימין",
      scen_subabi: "02. היפוך Subabi + מספר הפוך (84 ← 48)",
      scen_english: "03. מילה באנגלית בסוף משפט (FBI.)",
      scen_cp1255: "04. ג׳יבריש Windows-1255 ותו זר (דეייט)",
      tv_before_label: "לפני RightSub (תצוגה שבורה)",
      tv_after_label: "אחרי RightSub (תקן UAX #9 Rule N1)",
      inst_kicker: "CLI · WIZARD · MCP SERVER",
      install_title: "התקנה לעבודה מקומית, עונות שלמות ואוטומציה",
      install_subtitle:
        "מעבר לכלי הדפדפן, ניתן להתקין את חבילת ה-CLI המלאה הכוללת אשף אינטראקטיבי לטרמינל ול-CMD, חיבור לסוכני AI בפקודה אחת (<code>rightsub mcp --install</code>), ואוטומציה ל-qBittorrent / Sonarr / Bazarr.",
      tab_macos: "macOS &amp; Linux",
      tab_windows: "Windows (CMD / PowerShell)",
      tab_mcp: "סוכני AI (שרת MCP)",
      tab_docker: "Docker ואוטומציית *arr",
      mac_step1_title: "התקנה בפקודה אחת (Homebrew או סקריפט)",
      mac_step1_note:
        'או התקנה ישירה מ-GitHub:<code class="step-note-cmd" dir="ltr">git clone https://github.com/omerninyo/RightSub.git &amp;&amp; cd RightSub &amp;&amp; ./install.sh</code>',
      mac_step2_title: "הפעלת האשף האינטראקטיבי או תיקון אוטומטי",
      mac_step2_note:
        '<code dir="ltr">rightsub</code> פותח תפריט אינטראקטיבי עם גרירת קבצים; <code dir="ltr">rightsub auto</code> מתקן או מתרגם תיקייה שלמה.',
      win_step1_title: "מתקין אוטומטי לחלונות (רישום אוטומטי ל-PATH)",
      win_step1_note:
        "<code>install.bat</code> מאמת Python ו-FFmpeg ומוסיף את <code>rightsub</code> ל-PATH של המשתמש ללא צורך בהרשאות Administrator.",
      win_step2_title: "הרצה מכל חלון CMD או PowerShell",
      mcp_step1_title: "רישום אוטומטי לכל סוכני ה-AI בפקודה אחת",
      mcp_step1_note:
        "מזהה ורושם אוטומטית את שרת ה-MCP המקומי (8 כלים) ב-<strong>Google Antigravity</strong>, <strong>Claude Desktop</strong>, <strong>Cursor</strong>, <strong>Windsurf</strong> ו-<strong>Claude Code</strong>.",
      mcp_step2_title: "הנחיית הסוכן בשפה טבעית",
      cmd_mcp_prompt:
        '"בדוק את תיקיית המדיה ב-\u2066/Volumes/Media/Show\u2069, תקן את כתוביות העברית לפלקס במצב Seed-Safe, ואם חסר תרגום — חלץ את האנגלית ותרגם."',
      arr_step1_title: "מחולל Hooks ושירותי רקע אוטומטי",
      arr_step1_note:
        "מייצר סקריפטים מוכנים ל-qBittorrent ול-Transmission ב-<code>~/.config/rightsub/hooks/</code>, רושם Webhook ב-Sonarr/Radarr, ומתקין שירות רקע.",
      arr_step2_title: "שרת Webhook ו-Web UI מקומי (Port 8775)",
      copy_btn: "העתק",
      copied_btn: "הועתק",
      mat_kicker: "DETERMINISTIC VS. AI",
      matrix_title: "מתי מעורב AI ומתי המנוע רץ ב-0 טוקנים?",
      matrix_subtitle:
        "ב-99% מהכתוביות הקיימות בעברית אין שום צורך ב-AI. מודל שפה נדרש אך ורק לתרגום מאפס מאנגלית או לשיקום סמנטי של תרגומים ישנים:",
      mat_col_task: "פעולה / תרחיש שימוש",
      mat_col_cmd: "כלי / פקודה",
      mat_col_ai: "דורש מפתח AI?",
      mat_col_cost: "עלות טוקנים",
      mat_row1_task:
        "תיקון BiDi ופיסוק לפלקס, ביטול 18 תבניות Subabi, המרת CP1255, ניקוי פרסומות והומוגליפים",
      mat_row2_task:
        "אימות והיפוך מספרים דו-לשוני (<code>84</code> ← <code>48</code>) ותיקון מונחי קאנון",
      mat_row3_task:
        "בקרת איכות (QA), תאימות זמנים 1:1, גילוי Cue Drift וזיהוי שגיאות מגדר בפנייה",
      mat_row4_task:
        "ליטוש סמנטי של תרגום ישן/חובבני עם סקירה אינטראקטיבית שורה-אחר-שורה",
      mat_row5_task:
        "תרגום סרט או סדרה חדשים מאנגלית לעברית מאפס (כולל TMDb ו-Translation Bible)",
      no_ai: "לא (100% דטרמיניסטי)",
      no_ai_stage0: "לא (שלב 0 דטרמיניסטי)",
      no_ai_algo: "לא (100% אלגוריתמי)",
      opt_ai: "אופציונלי (למקרי קצה נדירים)",
      req_ai: "כן (או דרך סוכן ה-MCP)",
      footer_copy:
        "<strong>RightSub v1.5.0</strong> · קוד פתוח ברישיון MIT · 193 בדיקות אוטומטיות · עיבוד מקומי ב-100% ללא העלאת קבצים.",
      stat_cues: "כתוביות נסרקו",
      stat_fixed: "שורות תוקנו",
      stat_ads: "פרסומות הוסרו",
      stat_nums: "מספרים הופכו",
      subabi_unflipped: "היפוך Subabi תוקן · ",
      lines_mastered: "שורות תוקנו",
      foreign_protected:
        "קובץ זה זוהה ככתובית באנגלית/שפה זרה (מוגן משינוי).",
      download_btn: "הורד קובץ \u2066.he.srt\u2069",
      video_warn:
        "זהו קובץ וידאו. לחילוץ ותרגום של קובצי MKV/MP4 על הדיסק המקומי, הריצו בטרמינל: rightsub auto",
    },
    en: {
      dir: "ltr",
      toggleLabel: "עב",
      page_title: "RightSub — Hebrew Subtitle BiDi Mastering, Encoding Rescue & AI Suite",
      page_desc:
        "Open-source toolkit for fixing Hebrew subtitle punctuation and BiDi rendering in Plex, Infuse & Apple TV. Features an instant client-side browser studio, CLI wizard, Seed-Safe torrents, and native MCP server.",
      aria_home: "RightSub Home",
      aria_nav: "Primary Navigation",
      aria_theme: "Toggle color theme (Dark / Light)",
      aria_lang: "Switch language to Hebrew (החלף לעברית)",
      aria_gh: "GitHub Source Repository",
      aria_workbench: "SubRefine Interactive Studio",
      aria_wb_tabs: "Studio Mode",
      aria_scenarios: "Select Player Defect Scenario",
      aria_platforms: "Installation Platforms",
      skip_link: "Skip to main content",
      nav_studio: "Studio",
      nav_capabilities: "Features",
      nav_simulator: "Simulator",
      nav_install: "CLI & MCP",
      nav_architecture: "0-Token vs AI",
      hero_kicker: "OPEN-SOURCE SUBTITLE ENGINEERING · UAX #9 RULE N1",
      hero_title: "Hebrew Subtitle BiDi Mastering, Encoding Rescue & AI Translation.",
      hero_lead:
        "RightSub solves the rendering bugs that media players (Plex, Infuse, Apple TV, LG WebOS) fail to handle on their own: trailing question marks and periods jumping to the right edge, legacy visually pre-flipped subtitles (Subabi), Windows-1255 mojibake, and reversed 2-digit numbers.",
      pillar1_title: "100% Deterministic Local Mastering (0 Tokens)",
      pillar1_desc:
        "Technical repairs on existing subtitles run strictly via local algorithms — in your browser or terminal — with zero AI keys and zero cloud uploads.",
      pillar2_title: "Seed-Safe Torrent Protection",
      pillar2_desc:
        "Detects Hebrew content inside any plain <code>.srt</code> file, keeps the original torrent file untouched on disk, and writes a separate <code>.he.srt</code> file.",
      pillar3_title: "CLI Suite, Automation & Native MCP Server",
      pillar3_desc:
        "Full cross-platform package for macOS, Windows, and Docker with Sonarr/qBittorrent hooks and full English-to-Hebrew translation via AI agents or Ollama.",
      hero_cta_cli: "Install CLI & MCP Server",
      hero_cta_how: "How the Engine Works",
      wb_tab_file: "Fix .srt File",
      wb_tab_sandbox: "Live Line Sandbox",
      wb_privacy: "100% Local in Browser",
      drop_prompt: "Drag & drop Hebrew <code>.srt</code> file(s) here or click to browse",
      drop_subprompt:
        "Supports single files, multi-file batches, or a <code>Movie.srt</code> + <code>Movie.en.srt</code> pair to un-flip reversed 2-digit numbers (<code>84</code> → <code>48</code>).",
      opt_clean_ads: "Strip ad & credit banners",
      opt_clean_speakers: "Strip speaker labels (Alan:)",
      hero_cta_demo: "Load Broken Sample .srt",
      diff_heading: "Repaired Cues Inspector (Before vs. After)",
      diff_col_before: "Before (Broken Source)",
      diff_col_after: "After (RightSub + UAX #9)",
      sb_preset_label: "Presets:",
      sb_chip_1: "Jumping Punctuation",
      sb_chip_2: "Subabi Visual Flip",
      sb_chip_3: "Trailing English (FBI.)",
      sb_chip_4: "Foreign Glyph (דეייט) + Acronyms",
      sb_input_label: "Type or paste any Hebrew subtitle line to test live:",
      sb_out_broken: "Broken Player Rendering (Without RightSub)",
      sb_out_fixed: "Mastered Player Rendering (With RightSub)",
      sb_unicode_label: "Underlying Invisible Control Marks (Unicode View):",
      cap_kicker: "SYSTEM CAPABILITIES",
      cap_title: "What RightSub Actually Does",
      cap_subtitle:
        "RightSub separates its architecture into two engines: a zero-token deterministic mastering engine for existing subtitles (SubRefine), and an AI multi-agent translation engine (SubSwarm).",
      badge_deterministic: "100% Deterministic · 0 Tokens",
      badge_seedsafe: "Seed-Safe Torrents",
      badge_ai: "AI Agents / Ollama",
      cap1_title: "BiDi Punctuation Locking & Subabi Un-Flipping",
      cap1_desc:
        "Players like Plex and Apple TV render trailing punctuation (<code>?</code>, <code>!</code>, <code>.</code>) on the right side of Hebrew lines. Furthermore, thousands of older Hebrew subtitles were processed by visual-flipping tools (<code>Subabi</code>) that physically reversed periods and parentheses. RightSub detects file polarity, reverses 18 legacy flip patterns, and wraps lines in <strong>Unicode UAX #9 Rule N1</strong> <code>RLM</code> (<code>\\u200F</code>) marks.",
      cap2_title: "Windows-1255 Rescue, Homoglyphs & Bilingual Numbers",
      cap2_desc:
        'Byte-level detection of legacy <code dir="ltr">CP1255</code> / <code dir="ltr">ISO-8859-8</code> files converted cleanly to <code dir="ltr">UTF-8</code>. Normalizes lookalike foreign characters from 7 scripts (such as Georgian in <code dir="rtl">\u202Eד\u10D4ייט\u202C</code> → <code dir="rtl">דייט</code>), strips credit watermarks, and un-flips reversed 2-digit numbers (<code dir="ltr">84</code> → <code dir="ltr">48</code>) verified against companion English cues.',
      cap3_title: "Content-Based Hebrew Detection & Seed-Safe <code>.he.srt</code>",
      cap3_desc:
        "Downloaded a release with a plain <code>Movie.srt</code> or <code>Subs/</code> folder? RightSub inspects the file content, detects Hebrew automatically, leaves the source <code>.srt</code> 100% untouched on disk so qBittorrent/Transmission seeding never breaks, and outputs <code>Movie.he.srt</code> alongside the video.",
      cap4_title: "Full AI Translation & Native MCP Server",
      cap4_desc:
        "When no Hebrew subtitle exists, RightSub extracts embedded <code>.mkv</code>/<code>.mp4</code> tracks (or transcribes audio locally), builds a TMDb character gender bible (<code>את/היא</code> vs. <code>אתה/הוא</code>), and translates with strict 1:1 cue parity via its built-in MCP server (Claude, Cursor, Antigravity), Gemini, or local Ollama.",
      sim_kicker: "VISUAL COMPARISON",
      showcase_title: "Player Rendering Comparison: Before vs. After",
      showcase_subtitle:
        "Select a defect scenario to see how the exact same subtitle cue renders on a TV player before and after RightSub:",
      scen_punct: "01. Reversed Trailing Question Marks & Punctuation",
      scen_subabi: "02. Subabi Visual Flip + Reversed Number (84 → 48)",
      scen_english: "03. Sentence Ending with English Word (FBI.)",
      scen_cp1255: "04. Windows-1255 Gibberish & Foreign Glyph (דეייט)",
      tv_before_label: "Before RightSub (Broken Rendering)",
      tv_after_label: "After RightSub (UAX #9 Rule N1)",
      inst_kicker: "CLI · WIZARD · MCP SERVER",
      install_title: "Install for Local Media, Full Seasons & Automation",
      install_subtitle:
        "Beyond the browser studio, install the full CLI suite featuring an interactive terminal/CMD wizard, 1-command AI agent registration (<code>rightsub mcp --install</code>), and qBittorrent / Sonarr / Bazarr hooks.",
      tab_macos: "macOS &amp; Linux",
      tab_windows: "Windows (CMD / PowerShell)",
      tab_mcp: "AI Agents (MCP Server)",
      tab_docker: "Docker &amp; *arr Automation",
      mac_step1_title: "One-Command Install (Homebrew Tap or Script)",
      mac_step1_note:
        'Or directly from GitHub:<code class="step-note-cmd" dir="ltr">git clone https://github.com/omerninyo/RightSub.git &amp;&amp; cd RightSub &amp;&amp; ./install.sh</code>',
      mac_step2_title: "Launch Interactive Wizard or Autonomous Runner",
      mac_step2_note:
        '<code dir="ltr">rightsub</code> opens the interactive drag-and-drop wizard; <code dir="ltr">rightsub auto</code> fixes or translates an entire folder.',
      win_step1_title: "Automated Windows Installer (Auto-Configures PATH)",
      win_step1_note:
        "<code>install.bat</code> verifies Python & FFmpeg and registers <code>rightsub</code> in your User PATH without requiring Admin privileges.",
      win_step2_title: "Run from Any CMD or PowerShell Window",
      mcp_step1_title: "One-Command Multi-Agent MCP Registration",
      mcp_step1_note:
        "Detects and registers RightSub's local MCP Server (8 tools) in <strong>Google Antigravity</strong>, <strong>Claude Desktop</strong>, <strong>Cursor</strong>, <strong>Windsurf</strong>, and <strong>Claude Code</strong>.",
      mcp_step2_title: "Control via Natural Language",
      cmd_mcp_prompt:
        '"Inspect my media folder at /Volumes/Media/Show, fix all Hebrew subtitles for Plex in Seed-Safe mode, and if an episode is missing Hebrew subtitles, extract English and translate it."',
      arr_step1_title: "Automated Downloader Hooks & Background Service",
      arr_step1_note:
        "Generates ready-to-use qBittorrent & Transmission hooks in <code>~/.config/rightsub/hooks/</code>, registers Sonarr/Radarr webhooks, and installs OS background services.",
      arr_step2_title: "Container Webhook Daemon & Local Web UI (Port 8775)",
      copy_btn: "Copy",
      copied_btn: "Copied",
      mat_kicker: "DETERMINISTIC VS. AI",
      matrix_title: "When Is AI Used vs. 0-Token Deterministic Mode?",
      matrix_subtitle:
        "99% of existing Hebrew subtitles require zero AI keys. LLMs are used strictly for translating from scratch or polishing rare legacy drafts:",
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
      no_ai: "No (100% Deterministic)",
      no_ai_stage0: "No (Stage 0 Deterministic)",
      no_ai_algo: "No (100% Algorithmic)",
      opt_ai: "Optional (Rare Edge Cases)",
      req_ai: "Yes (or via MCP Agent)",
      footer_copy:
        "<strong>RightSub v1.5.0</strong> · MIT Open Source · 193 Automated Tests · 100% Local Processing.",
      stat_cues: "Cues Scanned",
      stat_fixed: "Lines Repaired",
      stat_ads: "Ads Stripped",
      stat_nums: "Numbers Un-Flipped",
      subabi_unflipped: "Subabi Un-Flipped · ",
      lines_mastered: "lines mastered",
      foreign_protected:
        "Foreign/English subtitle detected (protected from modification).",
      download_btn: "Download .he.srt",
      video_warn:
        "Video container detected. To extract and master MKV/MP4 files on disk, run locally: rightsub auto",
    },
  };

  const SANDBOX_PRESETS = {
    punct: 'שלום אלן, אתה חושב שבית המשפט של ארה"ב יקבל את זה?',
    subabi: ".שלום אלן, חיכינו לך במשרד הזה-",
    english: "ראיתי את הסוכנים של ה-FBI.",
    homoglyph: 'יצאת ל-ד\u10D4ייט עם עו"ד מבוסטון?',
  };

  const SCENARIOS = {
    punct: {
      before1: "?אלן, אתה באמת חושב שהשופט יקבל את זה",
      before2: "!אין לנו שום סיכוי בלי ראיות-",
      after1: "\u200Fאלן, אתה באמת חושב שהשופט יקבל את זה?\u200F",
      after2: "\u200F- אין לנו שום סיכוי בלי ראיות!\u200F",
      expBeforeHe:
        "ללא תו RLM סמוי אחרי סימן הפיסוק, אלגוריתם ה-BiDi של הנגן מפרש את סימן השאלה כתו ניטרלי בראש שורת LTR ומקפיץ אותו לימין.",
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
        "RightSub מזהה קוטביות הפוכה, משחזר את כל 18 תבניות ה-Subabi והסוגריים, ומצליב מול האנגלית כדי לתקן את 84 חזרה ל-48.",
      expBeforeEn:
        "Legacy visual flippers (Subabi) physically moved periods, dashes, parentheses, and reversed '48' into '84'.",
      expAfterEn:
        "RightSub reverses all 18 visual-flip patterns, restores parentheses, and cross-checks English cues to un-flip 84 -> 48.",
    },
    english: {
      before1: ".ראיתי את הסוכנים של ה-FBI",
      before2: "!זה תיק פדרלי של ה-CIA",
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
      before2: "סונכרן על ידי צוות טורק - Torec.net",
      after1: "\u200Fאני רוצה לצאת ל-דייט הערב.\u200F",
      after2He: "\u200F[שורת פרסומת וקרדיט הוסרה אוטומטית]\u200F",
      after2En: "[Ad & credit watermark stripped automatically]",
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
  let currentTheme = localStorage.getItem("rightsub_theme") || "dark";
  let currentScenario = "punct";
  let activeBlobUrls = [];
  let lastInputState = null;
  let daemonHealthData = null;

  function applyTheme(theme) {
    currentTheme = theme === "light" ? "light" : "dark";
    localStorage.setItem("rightsub_theme", currentTheme);
    document.documentElement.setAttribute("data-theme", currentTheme);

    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.setAttribute("aria-pressed", currentTheme === "light" ? "true" : "false");
    }
    const metaTheme = document.getElementById("meta-theme-color");
    if (metaTheme) {
      metaTheme.setAttribute("content", currentTheme === "light" ? "#fafafa" : "#09090b");
    }
  }

  function updateDaemonBadgeText() {
    if (!daemonHealthData) return;
    const badge = document.getElementById("daemon-status-badge");
    const text = document.getElementById("daemon-status-text");
    if (badge && text) {
      const count = daemonHealthData.metrics?.processed_count ?? 0;
      text.textContent =
        currentLang === "he"
          ? `שרת פעיל v${daemonHealthData.version} (${count} תוקנו)`
          : `Daemon v${daemonHealthData.version} (${count} mastered)`;
      badge.hidden = false;
    }
  }

  function applyLanguage(lang) {
    currentLang = lang in I18N ? lang : "he";
    localStorage.setItem("rightsub_lang", currentLang);
    const dict = I18N[currentLang];

    document.documentElement.lang = currentLang;
    document.documentElement.dir = dict.dir;
    document.title = dict.page_title;

    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute("content", dict.page_desc);
    const ogTitle = document.getElementById("og-title");
    if (ogTitle) ogTitle.setAttribute("content", dict.page_title);
    const ogDesc = document.getElementById("og-desc");
    if (ogDesc) ogDesc.setAttribute("content", dict.page_desc);

    const toggleLabel = document.getElementById("lang-toggle-label");
    if (toggleLabel) toggleLabel.textContent = dict.toggleLabel;

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });

    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      if (dict[key]) {
        el.setAttribute("aria-label", dict[key]);
      }
    });

    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      if (dict[key]) {
        el.setAttribute("title", dict[key]);
      }
    });

    document.querySelectorAll("[data-label-i18n]").forEach((el) => {
      const key = el.getAttribute("data-label-i18n");
      if (dict[key]) {
        el.setAttribute("data-label", dict[key]);
      }
    });

    renderScenario(currentScenario);
    updateLiveSandbox();
    updateDaemonBadgeText();

    if (lastInputState) {
      reprocessLastInput();
    }
  }

  function simulateBrokenSingleLine(rawLine) {
    const clean = String(rawLine || "")
      .replace(/<[^>]+>|\{\\[^}]+\}/g, "")
      .replace(/[\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, "")
      .trim();
    if (!clean) return "";

    // Leading dialogue dash + trailing punctuation -> move punctuation to start and dash to end
    const mDash = clean.match(/^([-–—])\s*(.+?)([?!.:,;…]+)$/);
    if (mDash && /[\u0590-\u05FF]/.test(mDash[2])) {
      return `${mDash[3]}${mDash[2].trim()}${mDash[1]}`;
    }

    // Normal logical line ending with punctuation -> move punctuation to index 0 (visual right in dir="rtl")
    const m = clean.match(/^(.+?)([?!.:,;…]+)$/);
    if (m && /[\u0590-\u05FF]/.test(m[1])) {
      return `${m[2]}${m[1]}`;
    }
    return clean;
  }

  function simulateBrokenPlayerView(rawText) {
    return String(rawText || "")
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l.length > 0)
      .map(simulateBrokenSingleLine)
      .join("\n");
  }

  function updateLiveSandbox() {
    if (!window.RightSubRefine) return;
    const inputEl = document.getElementById("sandbox-input");
    const beforeEl = document.getElementById("sb-render-before");
    const afterEl = document.getElementById("sb-render-after");
    const unicodeEl = document.getElementById("sb-unicode-raw");
    if (!inputEl || !beforeEl || !afterEl || !unicodeEl) return;

    const rawLines = (inputEl.value || "")
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l.length > 0);
    const cleanRaw = rawLines.join("\n");

    const wrappedSrt = `1\n00:00:01,000 --> 00:00:04,000\n${cleanRaw}\n`;
    const res = window.RightSubRefine.processSrtContent(wrappedSrt, {
      cleanAds: false,
      cleanSpeakers: false,
    });
    const outLines = res.resultText.trim().split("\n");
    const masteredLine = outLines.slice(2).join("\n").trim();

    beforeEl.textContent = simulateBrokenPlayerView(cleanRaw);
    afterEl.textContent = masteredLine;
    unicodeEl.textContent = masteredLine.replace(
      /\u200F/g,
      "\u200F\u2066[RLM]\u2069\u200F"
    );
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
    if (a2) {
      if (sc.after2He && sc.after2En) {
        a2.textContent = currentLang === "he" ? sc.after2He : sc.after2En;
        a2.dir = currentLang === "he" ? "rtl" : "ltr";
      } else {
        a2.textContent = sc.after2;
        a2.dir = "rtl";
      }
    }
    if (expB) expB.textContent = currentLang === "he" ? sc.expBeforeHe : sc.expBeforeEn;
    if (expA) expA.textContent = currentLang === "he" ? sc.expAfterHe : sc.expAfterEn;
  }

  function revokeActiveBlobs() {
    for (const u of activeBlobUrls) {
      try {
        URL.revokeObjectURL(u);
      } catch (_) {}
    }
    activeBlobUrls = [];
  }

  function renderResults(processedFiles) {
    const dict = I18N[currentLang];
    const resultsContainer = document.getElementById("fixer-results");
    const statsGrid = document.getElementById("stats-grid");
    const downloadsList = document.getElementById("downloads-list");
    const diffWrapper = document.getElementById("diff-preview-wrapper");
    const diffTbody = document.getElementById("diff-tbody");

    if (!resultsContainer || !statsGrid || !downloadsList) return;

    revokeActiveBlobs();

    let totalSubs = 0;
    let totalFixed = 0;
    let totalAds = 0;
    let totalNums = 0;
    const allDiffs = [];

    downloadsList.innerHTML = "";

    for (const item of processedFiles) {
      if (item.errorKey || item.error) {
        const errMsg = item.errorKey ? dict[item.errorKey] : item.error;
        const errDiv = document.createElement("div");
        errDiv.className = "download-item";
        errDiv.innerHTML = `<div class="download-meta"><span class="download-filename">${escapeHtml(
          item.name
        )}</span><span class="download-submeta" style="color:var(--danger-text)">${escapeHtml(
          errMsg
        )}</span></div>`;
        downloadsList.appendChild(errDiv);
        continue;
      }

      totalSubs += item.stats.totalSubs;
      totalFixed += item.stats.modifiedLines;
      totalAds += item.stats.adsRemoved;
      totalNums += item.stats.numbersUnflipped;

      const candidates = item.stats.sampleDiffs.some((d) => d.visualChange)
        ? item.stats.sampleDiffs.filter((d) => d.visualChange)
        : item.stats.sampleDiffs;

      for (const d of candidates) {
        if (allDiffs.length < 20) {
          allDiffs.push(d);
        }
      }

      const blob = new Blob([item.stats.resultText], {
        type: "text/plain;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);
      activeBlobUrls.push(url);

      const row = document.createElement("div");
      row.className = "download-item";
      row.innerHTML = `
        <div class="download-meta">
          <span class="download-filename">${escapeHtml(item.outName)}</span>
          <span class="download-submeta">
            \u2066${escapeHtml(item.encoding.toUpperCase())} → UTF-8\u2069 ·
            ${item.stats.isPreflippedFile ? escapeHtml(dict.subabi_unflipped) : ""}${
        item.stats.modifiedLines
      } ${escapeHtml(dict.lines_mastered)}
          </span>
        </div>
        <a href="${url}" download="${escapeHtml(
        item.outName
      )}" class="btn btn-solid">${escapeHtml(dict.download_btn)}</a>
      `;
      downloadsList.appendChild(row);
    }

    statsGrid.innerHTML = `
      <div class="stat-box">
        <div class="stat-value">${totalSubs}</div>
        <div class="stat-label">${escapeHtml(dict.stat_cues)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalFixed}</div>
        <div class="stat-label">${escapeHtml(dict.stat_fixed)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalAds}</div>
        <div class="stat-label">${escapeHtml(dict.stat_ads)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${totalNums}</div>
        <div class="stat-label">${escapeHtml(dict.stat_nums)}</div>
      </div>
    `;

    if (allDiffs.length > 0 && diffWrapper && diffTbody) {
      diffTbody.innerHTML = allDiffs
        .map(
          (d) => `
        <tr>
          <td data-label="#"><span dir="ltr">#${d.cue}</span></td>
          <td class="diff-before" data-label="${escapeHtml(
            dict.diff_col_before
          )}" data-label-i18n="diff_col_before">
            <span class="diff-line" dir="rtl">${escapeHtml(
              simulateBrokenPlayerView(d.before)
            )}</span>
          </td>
          <td class="diff-after" data-label="${escapeHtml(
            dict.diff_col_after
          )}" data-label-i18n="diff_col_after">
            <span class="diff-line" dir="rtl">${escapeHtml(d.after)}</span>
          </td>
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

  function getBaseStem(filename) {
    return String(filename || "")
      .replace(/\.(he|heb|en|eng|hi|sdh)\.srt$/i, "")
      .replace(/\.srt$/i, "")
      .toLowerCase();
  }

  function processDecodedEntries(decodedFiles) {
    if (!window.RightSubRefine) return;
    const dict = I18N[currentLang];
    const cleanAds = document.getElementById("opt-clean-ads")?.checked ?? true;
    const cleanSpeakers =
      document.getElementById("opt-clean-speakers")?.checked ?? false;

    const enFiles = decodedFiles.filter((f) => !f.isVideo && !f.isHebrew);
    const hasHebrewFiles = decodedFiles.some((f) => !f.isVideo && f.isHebrew);

    const processed = [];
    for (const f of decodedFiles) {
      if (f.isVideo) {
        processed.push({
          name: f.name,
          error: `${dict.video_warn} "${f.name}"`,
        });
        continue;
      }
      if (!f.isHebrew && hasHebrewFiles) {
        continue;
      }
      if (!f.isHebrew) {
        processed.push({
          name: f.name,
          errorKey: "foreign_protected",
        });
        continue;
      }

      const stem = getBaseStem(f.name);
      const matchedEn =
        enFiles.find((ef) => getBaseStem(ef.name) === stem) || enFiles[0] || null;

      const stats = window.RightSubRefine.processSrtContent(f.text, {
        cleanAds,
        cleanSpeakers,
        enContent: matchedEn ? matchedEn.text : null,
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

  async function handleFiles(fileList) {
    if (!fileList || fileList.length === 0 || !window.RightSubRefine) return;

    const decodedFiles = [];
    for (const file of Array.from(fileList)) {
      const lower = file.name.toLowerCase();
      if (/\.(mkv|mp4|avi|mov|m4v)$/.test(lower)) {
        decodedFiles.push({
          name: file.name,
          isVideo: true,
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

    lastInputState = { type: "files", decodedFiles };
    processDecodedEntries(decodedFiles);
  }

  function runDemoSample() {
    if (!window.RightSubRefine) return;
    lastInputState = { type: "demo" };
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

  function reprocessLastInput() {
    if (!lastInputState) return;
    if (lastInputState.type === "demo") {
      runDemoSample();
    } else if (lastInputState.type === "files") {
      processDecodedEntries(lastInputState.decodedFiles);
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async function checkLocalDaemonHealth() {
    try {
      const resp = await fetch("/health", { cache: "no-store" });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data && data.status === "healthy") {
        daemonHealthData = data;
        updateDaemonBadgeText();
      }
    } catch (_) {}
  }

  function bindTablistKeyboard(tablistSelector, tabSelector) {
    const tablist = document.querySelector(tablistSelector);
    if (!tablist) return;
    tablist.addEventListener("keydown", function (e) {
      const tabs = Array.from(tablist.querySelectorAll(tabSelector));
      const idx = tabs.indexOf(document.activeElement);
      if (idx === -1) return;

      const isRtl = document.documentElement.dir === "rtl";
      const nextKey = isRtl ? "ArrowLeft" : "ArrowRight";
      const prevKey = isRtl ? "ArrowRight" : "ArrowLeft";

      let targetIdx = -1;
      if (e.key === nextKey) {
        targetIdx = (idx + 1) % tabs.length;
      } else if (e.key === prevKey) {
        targetIdx = (idx - 1 + tabs.length) % tabs.length;
      } else if (e.key === "Home") {
        targetIdx = 0;
      } else if (e.key === "End") {
        targetIdx = tabs.length - 1;
      }

      if (targetIdx !== -1) {
        e.preventDefault();
        tabs[targetIdx].focus();
        tabs[targetIdx].click();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(currentTheme);
    applyLanguage(currentLang);
    checkLocalDaemonHealth();

    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        applyTheme(currentTheme === "dark" ? "light" : "dark");
      });
    }

    const langBtn = document.getElementById("lang-toggle");
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        applyLanguage(currentLang === "he" ? "en" : "he");
      });
    }

    // Workbench mode switcher (File Drop vs Live Line Sandbox)
    document.querySelectorAll(".wb-tab").forEach((tab) => {
      tab.addEventListener("click", function () {
        const mode = this.getAttribute("data-wb-mode");
        document.querySelectorAll(".wb-tab").forEach((t) => {
          t.classList.remove("active");
          t.setAttribute("aria-selected", "false");
          t.setAttribute("tabindex", "-1");
        });
        this.classList.add("active");
        this.setAttribute("aria-selected", "true");
        this.setAttribute("tabindex", "0");

        const filePanel = document.getElementById("wb-panel-file");
        const sbPanel = document.getElementById("wb-panel-sandbox");
        if (filePanel && sbPanel) {
          filePanel.hidden = mode !== "file";
          sbPanel.hidden = mode !== "sandbox";
        }
        if (mode === "sandbox") updateLiveSandbox();
      });
    });
    bindTablistKeyboard(".workbench-tabs", ".wb-tab");

    // Live Sandbox presets & textarea listener
    const sbInput = document.getElementById("sandbox-input");
    if (sbInput) {
      sbInput.addEventListener("input", function () {
        const val = sbInput.value;
        document.querySelectorAll(".chip-btn").forEach((c) => {
          const key = c.getAttribute("data-sb-preset");
          const isMatch = SANDBOX_PRESETS[key] === val;
          c.classList.toggle("active", isMatch);
          c.setAttribute("aria-pressed", isMatch ? "true" : "false");
        });
        updateLiveSandbox();
      });
    }

    document.querySelectorAll(".chip-btn").forEach((chip) => {
      chip.addEventListener("click", function () {
        document.querySelectorAll(".chip-btn").forEach((c) => {
          c.classList.remove("active");
          c.setAttribute("aria-pressed", "false");
        });
        this.classList.add("active");
        this.setAttribute("aria-pressed", "true");
        const key = this.getAttribute("data-sb-preset");
        if (sbInput && SANDBOX_PRESETS[key]) {
          sbInput.value = SANDBOX_PRESETS[key];
          updateLiveSandbox();
        }
      });
    });

    const demoBtn = document.getElementById("load-demo-btn");
    if (demoBtn) {
      demoBtn.addEventListener("click", runDemoSample);
    }

    document.getElementById("opt-clean-ads")?.addEventListener("change", reprocessLastInput);
    document.getElementById("opt-clean-speakers")?.addEventListener("change", reprocessLastInput);

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
      fileInput.addEventListener("change", async (e) => {
        await handleFiles(e.target.files);
        fileInput.value = "";
      });

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
        document.querySelectorAll(".scenario-btn").forEach((b) => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
          b.setAttribute("tabindex", "-1");
        });
        this.classList.add("active");
        this.setAttribute("aria-selected", "true");
        this.setAttribute("tabindex", "0");
        const simPanel = document.getElementById("simulator-panel");
        if (simPanel && this.id) {
          simPanel.setAttribute("aria-labelledby", this.id);
        }
        renderScenario(this.getAttribute("data-scenario"));
      });
    });
    bindTablistKeyboard(".scenario-bar", ".scenario-btn");

    // Installation Tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const target = this.getAttribute("data-tab");
        document.querySelectorAll(".tab-btn").forEach((b) => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
          b.setAttribute("tabindex", "-1");
        });
        this.classList.add("active");
        this.setAttribute("aria-selected", "true");
        this.setAttribute("tabindex", "0");

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
    bindTablistKeyboard(".platform-tabs", ".tab-btn");

    // Copy buttons
    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", async function () {
        const targetId = this.getAttribute("data-copy-target");
        const codeEl = document.getElementById(targetId);
        if (!codeEl) return;
        try {
          const cleanCode = codeEl.textContent
            .replace(/[\u2066-\u2069]/g, "")
            .trim();
          await navigator.clipboard.writeText(cleanCode);
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
