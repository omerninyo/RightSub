/**
 * subrefine.js — RightSub Client-Side SubRefine Mastering Engine (v1.5.1)
 * ----------------------------------------------------------------------
 * 100% browser-local & Node.js compatible port of `scripts/07_fix_plex_punctuation.py`.
 * Zero server uploads. Zero external dependencies.
 *
 * Capabilities:
 * 1. Byte-level encoding detection (`UTF-16 BOM`, `UTF-8`, `Windows-1255` vs `Windows-1252`).
 * 2. Multi-lingual homoglyph normalization across 7 scripts (including Georgian `דეייט` -> `דייט`).
 * 3. Safe final-letter normalization (`normalizeFinalLetters`) triggered strictly on homoglyph repair.
 * 4. File-level polarity detection (`detectFileFlipPolarity`) & 18-pattern legacy visual un-flipping (`Subabi`).
 * 5. Deterministic bilingual 2-digit number cross-check (`crossCheckBilingualNumbers`, `84` -> `48`).
 * 6. Ad & multi-line credit banner stripping (`Torec`, `Wizdom`, `SubCenter`, `OpenSubtitles`, Telegram).
 * 7. Idempotent Unicode UAX #9 Rule N1 RLM (`\u200F`) wrapping for Plex, Infuse, Apple TV & Smart TVs.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.RightSubRefine = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const RLM = "\u200F";

  const AD_PATTERNS = [
    /\bopensubtitles\b/i,
    /\btorec(?:\.net)?\b/i,
    /\bwizdom(?:\.xyz)?\b/i,
    /\bsratim\.co\.il\b/i,
    /\bsubcenter\b/i,
    /\bktuvit\b/i,
    /סונכרן\s+(?:על\s+ידי|ע["״']?י)/i,
    /תורגם\s+(?:על\s+ידי|ע["״']?י)/i,
    /^[\u200F\s\-–—]*(?:מלאכת\s+)?ה?תרגום\s*:\s*\S+/i,
    /^[\u200F\s\-–—]*(?:מלאכת\s+)?ה?סנכרון\s*:\s*\S+/i,
    /הורד\s+מ[-–—]\s*(?!\d)(?:אתר|[A-Za-z0-9\-]+\.[A-Za-z]{2,}|טורק|כתובית|סאבסנטר|וויזדום)/i,
    /^[\u200e\u200f\s\-–—]*(?:הועלה|סונכרן\s+ו?הועלה)\s+על\s+ידי/i,
    /הצטרפו\s+ל.*טלגרם/i,
    /t\.me\//i,
    /telegram\.me/i,
    /rip\s+by\b/i,
    /sync\s+by\b/i,
  ];

  const DANGLING_CREDIT_REGEX =
    /(?:על\s+ידי|ע["״']?י|(?:מלאכת\s+)?ה?(?:תרגום|סנכרון)\s*:|הועלה\s+על\s+ידי|synced\s+by|translated\s+by)\s*$/i;

  const ARABIC_TO_HEBREW = {
    "\u0645": "מ",
    "\u064A": "י",
    "\u0648": "ו",
    "\u0647": "ה",
    "\u0646": "נ",
    "\u0631": "ר",
    "\u062F": "ד",
    "\u0633": "ס",
    "\u0643": "כ",
    "\u0628": "ב",
    "\u062A": "ת",
    "\u0644": "ל",
    "\u0642": "ק",
    "\u0635": "צ",
    "\u0637": "ט",
    "\u0639": "ע",
    "\u062D": "ח",
    "\u062E": "ח",
    "\u062C": "ג",
    "\u0632": "ז",
    "\u0641": "פ",
    "\u0634": "ש",
    "\u0627": "א",
    "\u0623": "א",
    "\u0621": "א",
    "\u0626": "י",
    "\u0624": "ו",
    "\u0625": "א",
    "\u0622": "א",
    "\u0629": "ה",
    "\u0649": "י",
    "\u0630": "ד",
    "\u0636": "צ",
    "\u0638": "ט",
    "\u063A": "ג",
  };

  const ARABIC_PHRASES = [
    [/(?<![א-ת\u0600-\u06FF])כל\s*ما(?![א-ת\u0600-\u06FF])/g, "כל מה"],
    [/(?<![א-ת\u0600-\u06FF])ما(?![א-ת\u0600-\u06FF])/g, "מה"],
    [/(?<![א-ת\u0600-\u06FF])كل\s+ما(?![א-ת\u0600-\u06FF])/g, "כל מה"],
    [/(?<![א-ת\u0600-\u06FF])تكون(?![א-ת\u0600-\u06FF])/g, "תהיה"],
    [/(?<![א-ת\u0600-\u06FF])يكون(?![א-ת\u0600-\u06FF])/g, "יהיה"],
    [/(?<![א-ת\u0600-\u06FF])اكون(?![א-ת\u0600-\u06FF])/g, "אהיה"],
    [/(?<![א-ת\u0600-\u06FF])أكون(?![א-ת\u0600-\u06FF])/g, "אהיה"],
    [/(?<![א-ת\u0600-\u06FF])بالכאד(?![א-ת\u0600-\u06FF])/g, "בקושי"],
    [/(?<![א-ת\u0600-\u06FF])بالكاد(?![א-ת\u0600-\u06FF])/g, "בקושי"],
    [/(?<![א-ת\u0600-\u06FF])هي(?![א-ת\u0600-\u06FF])/g, "היא"],
    [/(?<![א-ת\u0600-\u06FF])هو(?![א-ת\u0600-\u06FF])/g, "הוא"],
  ];

  const CYRILLIC_TO_HEBREW = {
    м: "מ",
    М: "מ",
    а: "א",
    А: "א",
    р: "ר",
    Р: "ר",
    с: "ס",
    С: "ס",
    т: "ת",
    Т: "ת",
    х: "ח",
    Х: "ח",
    о: "ס",
    О: "ס",
    е: "ה",
    Е: "ה",
    в: "ב",
    В: "ב",
    н: "נ",
    Н: "נ",
    и: "י",
    И: "י",
    к: "כ",
    К: "כ",
    у: "ו",
    У: "ו",
  };

  const UNIVERSAL_HOMOGLYPH_MAP = {
    "\u10D7": "ת",
    "\u10D0": "א",
    "\u10D9": "ק",
    "\u10D4": "ה",
    "\u10DA": "ל",
    "\u0578": "ו",
    "\u056B": "י",
    "\u0574": "מ",
    "\u03C2": "ס",
    "\u03C4": "ט",
    "\u03BF": "ו",
    "\u03BD": "ן",
    "\u03B5": "ה",
    "\u0F62": "ר",
    "\u0F0B": "",
    "\u0E01": "ק",
    "\u0E34": "",
    "\u30E1": "מ",
    "\u30EA": "ר",
    "\u30AB": "ק",
  };

  const UNIVERSAL_PHRASES = [
    [/השופט[\u03BF][\u03C2]/g, "השופט"],
    [/האחרו[נן\u03BD][ה\u03B5][ס\u03C2]/g, "האחרונות"],
    [/מב[\u0578]ס[\u03C4][\u03BF][\u03BD]/g, "מבוסטון"],
    [/בא[\u30E1][ר\u30EA][ק\u30AB]ה?/g, "באמריקה"],
    [/לא\s*מ[\u0565\u10D4][ל\u10DA]רוז/g, "לא מלרוז"],
    [/מר\s*מ[\u0995\u09C7\u09AC\u09BE\u0C2C\u0C3E]+/g, "מר מקבה"],
    [/פ[ר\u0F62\u0F0B]+סה/g, "פארסה"],
    [/ג([׳'])ק\s*בוסט[יק\u0E01\u0E34]+/g, "ג$1ק בוסטיק"],
    [/מתקד[ימ\u056B\u0574]+ם/g, "מתקדמים"],
    [/קרויצפלד[- ]י[א\u10D0][ק\u10D9]וב/g, "קרויצפלד-יאקוב"],
    [/ה[ת\u10D7]זת/g, "התזת"],
    [/(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?ד[\u10D4]ייט(?![א-ת])/g, "$1דייט"],
    [/[\u585A]/g, ""],
    [/\\"/g, '"'],
    [/(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קאבתן(?![א-ת])/g, "$1קברניט"],
    [/(?<![א-ת])לשום\s+את(?![א-ת])/g, "לשים את"],
    [/(?<![א-ת])מוחב\s+אותנו(?![א-ת])/g, "מושכת אותנו"],
    [/(?<![א-ת])(ו)?ירתי(?=\s+(?:בו|בה|בהם|בהן|לעבר|באוויר|כדור))/g, "$1יריתי"],
    [/(?<![א-ת])(ש)?הודאת(?=\s+(?:תחת|בכך|בפני|כי|על))/g, "$1הודית"],
  ];

  const DISALLOWED_FOREIGN_SCRIPTS =
    /[\u0600-\u06FF\u0400-\u04FF\u0370-\u03FF\u0530-\u058F\u10A0-\u10FF\u0900-\u0DFF\u0E00-\u0E7F\u0F00-\u0FFF\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF\u3400-\u4DBF\u2E80-\u2EFF\uAC00-\uD7AF]/g;

  const BIDI_CONTROL_CHARS_REGEX = /[\u200e\u200f\u202a-\u202e\u2066-\u2069]/g;

  const SPEAKER_TAG_REGEX =
    /^((?:\{\\[^}]+\}\s*)*(?:<(?:[iIuUbB]|font\b[^>]*)>\s*)*)[\u200e\u200f\u202a-\u202e\u2066-\u2069\s]*(?:[-–—]\s*)?(?:(?:אלן|דני|שירלי|פול|בראד|לורי|טרה|סאלי|דניס|קייטי|ג['׳]רי|בברלי|אדווין|אישה|גבר|דובר|דוברת|שופט|שופטת|השופט|השופטת|קול|קריין|קריינית|כולם|שוטר|שוטרת|ילד|ילדה|רופא|רופאה|אחות|עד(?!\s+\d+\s*:\s*\d)|עדה|סוכן|סוכנת)(?:\s+\d+)?:(?:\s+|$)|\[\s*(?:לוחש|לוחשת|לוחשים|לוחש\/ת)\s*\]\s+(?=[\u0590-\u05FFA-Za-z]))/i;

  /**
   * Decodes raw subtitle bytes (ArrayBuffer or Uint8Array) with automatic
   * UTF-16 BOM, strict UTF-8, and Windows-1255 (Hebrew) vs Windows-1252 detection.
   */
  function decodeSrtBuffer(buffer) {
    const bytes =
      buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer || []);
    if (bytes.length === 0) {
      return { text: "", encoding: "utf-8" };
    }

    // 1. Check UTF-16 BOM
    if (bytes.length >= 2) {
      if (bytes[0] === 0xff && bytes[1] === 0xfe) {
        return {
          text: new TextDecoder("utf-16le").decode(bytes.subarray(2)),
          encoding: "utf-16",
        };
      }
      if (bytes[0] === 0xfe && bytes[1] === 0xff) {
        return {
          text: new TextDecoder("utf-16be").decode(bytes.subarray(2)),
          encoding: "utf-16",
        };
      }
    }

    // 2. Try strict UTF-8
    try {
      const utf8Decoder = new TextDecoder("utf-8", { fatal: true });
      let text = utf8Decoder.decode(bytes);
      if (text.charCodeAt(0) === 0xfeff) {
        text = text.slice(1);
      }
      return { text, encoding: "utf-8" };
    } catch (_) {
      // Fall through to legacy 8-bit charset heuristics
    }

    // 3. Distinguish Windows-1255 (Hebrew ANSI) from Windows-1252 (Western European ANSI)
    let cp1255HebrewBytes = 0;
    let consecutiveHebrewWords = 0;
    let currentRun = 0;
    let asciiAlphaBytes = 0;

    for (let i = 0; i < bytes.length; i++) {
      const b = bytes[i];
      if (b >= 0xe0 && b <= 0xfa) {
        cp1255HebrewBytes++;
        currentRun++;
      } else {
        if (currentRun >= 2) {
          consecutiveHebrewWords++;
        }
        currentRun = 0;
      }
      if ((b >= 0x41 && b <= 0x5a) || (b >= 0x61 && b <= 0x7a)) {
        asciiAlphaBytes++;
      }
    }
    if (currentRun >= 2) {
      consecutiveHebrewWords++;
    }

    if (
      cp1255HebrewBytes >= 4 &&
      (consecutiveHebrewWords >= 2 ||
        (consecutiveHebrewWords >= 1 &&
          cp1255HebrewBytes > asciiAlphaBytes * 0.5))
    ) {
      try {
        const text = new TextDecoder("windows-1255").decode(bytes);
        return { text, encoding: "windows-1255" };
      } catch (_) {
        // Fallback if windows-1255 decoder is unavailable
      }
    }

    try {
      return {
        text: new TextDecoder("windows-1252").decode(bytes),
        encoding: "cp1252",
      };
    } catch (_) {
      return {
        text: new TextDecoder("utf-8").decode(bytes),
        encoding: "utf-8-fallback",
      };
    }
  }

  function normalizeFinalLetters(text) {
    const punct = "(?:[\\u200F\\s\\.\\?!,:;\\–\\—\\)\\]»…]|[\"'״׳”’](?![א-ת])|$)";
    text = text.replace(
      new RegExp("(?<=[א-ת])(?<![כך])כ(?=" + punct + ")", "g"),
      "ך"
    );
    text = text.replace(
      new RegExp("(?<=[א-ת])(?<![מם])מ(?=" + punct + ")", "g"),
      "ם"
    );
    text = text.replace(
      new RegExp("(?<=[א-ת])(?<![נן])נ(?=" + punct + ")", "g"),
      "ן"
    );
    text = text.replace(
      new RegExp("(?<=[א-ת])(?<![צץ])צ(?=" + punct + ")", "g"),
      "ץ"
    );

    text = text.replace(/(?<![א-תa-zA-Z0-9])ם-(?=\d|[א-תa-zA-Z])/g, "מ-");
    text = text.replace(/(?<![א-תa-zA-Z0-9])ך-(?=\d|[א-תa-zA-Z])/g, "כ-");
    text = text.replace(/(?<![א-תa-zA-Z0-9])ן-(?=\d|[א-תa-zA-Z])/g, "נ-");
    text = text.replace(/(?<![א-תa-zA-Z0-9])ף-(?=\d|[א-תa-zA-Z])/g, "פ-");
    text = text.replace(/(?<![א-תa-zA-Z0-9])ץ-(?=\d|[א-תa-zA-Z])/g, "צ-");
    return text;
  }

  function cleanAndSanitizeText(text) {
    if (!text) return "";

    let ssaLead = "";
    const ssaMatch = text.match(/^\s*((?:\{\\[^}]+\}\s*)+)([\s\S]*)$/);
    if (ssaMatch) {
      ssaLead = ssaMatch[1].replace(/\s+/g, "");
      text = ssaMatch[2];
    }

    text = text.replace(/<truncated\s+\d+\s+bytes>/g, "");

    const hasJsonLeak = /(?:["'](?:hebrew|index|text)["']|(?<![A-Za-z])(?:hebrew|index))\s*:/.test(
      text
    );
    if (hasJsonLeak) {
      text = text.replace(
        /(?:["'](?:hebrew|text)["']|(?<![A-Za-z])hebrew)\s*:\s*["']?/g,
        ""
      );
      text = text.replace(
        /(?:["']index["']|(?<![A-Za-z])index)\s*:\s*\d+,?/g,
        ""
      );
      text = text.replace(/^\s*[\{\}\[\]]+\s*/g, "");
      text = text.replace(/\s*[\{\}\[\]]+\s*$/g, "");
    } else {
      text = text.replace(/^\s*[\{\}]+\s*/g, "");
      text = text.replace(/\s*[\{\}]+\s*$/g, "");
    }

    text = text.replace(/\\n/g, "\n").replace(/\\r/g, "").replace(/\\"/g, '"');
    text = text.replace(/[\uFB1D-\uFDFF\uFE70-\uFEFF]+/g, (m) =>
      m.normalize("NFKD")
    );

    text = text.replace(/א\u05B4מ\u05B8?ם/g, "אימם");
    text = text.replace(/(?<=אביהם וגם )אמם(?![א-ת])/g, "אימם");
    text = text.replace(/[\u0591-\u05BD\u05BF-\u05C7]/g, "");

    for (const [pattern, repl] of UNIVERSAL_PHRASES) {
      text = text.replace(pattern, repl);
    }
    for (const [pattern, repl] of ARABIC_PHRASES) {
      text = text.replace(pattern, repl);
    }

    let hadHomoglyph = false;
    if (/[\u064B-\u065F\u0670]/.test(text)) {
      text = text.replace(/[\u064B-\u065F\u0670]/g, "");
      hadHomoglyph = true;
    }

    for (const [cyr, he] of Object.entries(CYRILLIC_TO_HEBREW)) {
      if (text.includes(cyr)) {
        text = text.split(cyr).join(he);
        hadHomoglyph = true;
      }
    }
    for (const [ar, he] of Object.entries(ARABIC_TO_HEBREW)) {
      if (text.includes(ar)) {
        text = text.split(ar).join(he);
        hadHomoglyph = true;
      }
    }
    for (const [fg, he] of Object.entries(UNIVERSAL_HOMOGLYPH_MAP)) {
      if (text.includes(fg)) {
        text = text.split(fg).join(he);
        hadHomoglyph = true;
      }
    }

    if (hadHomoglyph) {
      text = normalizeFinalLetters(text);
    }

    text = text.replace(/(?<![א-ת])אמם(?![א-ת])/g, "אממ");
    text = text.replace(/(?<![א-ת])המם(?![א-ת])/g, "הממ");
    text = text.replace(/(?<![א-ת])ממם(?![א-ת])/g, "מממ");
    text = text.replace(/(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?טרמף(?![א-ת])/g, "$1טרמפ");

    text = text.replace(DISALLOWED_FOREIGN_SCRIPTS, "");
    text = text.replace(/[\u0591-\u05BD\u05BF-\u05C7]/g, "");
    text = text.replace(/[ \t]+/g, " ").trim();

    return ssaLead ? `${ssaLead}${text}` : text;
  }

  function detectHebrew(content, minChars = 6, minRatio = 0.15) {
    const hebrewMatches = content.match(/[\u0590-\u05FF]/g) || [];
    const latinMatches = content.match(/[a-zA-Z]/g) || [];
    const hebrewChars = hebrewMatches.length;
    const latinChars = latinMatches.length;
    const totalAlpha = hebrewChars + latinChars;

    if (totalAlpha === 0) {
      return {
        isHebrew: false,
        ratio: 0.0,
        details: "No alphabetic characters found",
      };
    }

    const ratio = hebrewChars / totalAlpha;
    const isHebrew =
      (hebrewChars >= minChars || (latinChars === 0 && hebrewChars >= 3)) &&
      ratio >= minRatio;
    return {
      isHebrew,
      ratio,
      details: `Hebrew chars: ${hebrewChars}, Latin chars: ${latinChars} (Hebrew ratio: ${(
        ratio * 100
      ).toFixed(1)}%)`,
    };
  }

  function stripTagsAndBidi(line) {
    return line
      .replace(/<[^>]+>|\{\\[^}]+\}/g, "")
      .replace(BIDI_CONTROL_CHARS_REGEX, "")
      .trim();
  }

  function isAdLine(line) {
    const clean = stripTagsAndBidi(line);
    return AD_PATTERNS.some((rx) => rx.test(clean));
  }

  function filterAdLinesFromBlock(lines) {
    const kept = [];
    let removed = 0;
    let skipNext = false;

    for (let idx = 0; idx < lines.length; idx++) {
      const l = lines[idx];
      if (skipNext) {
        removed++;
        skipNext = false;
        continue;
      }
      if (isAdLine(l)) {
        removed++;
        const cleanCurr = stripTagsAndBidi(l);
        const lowerCurr = l.toLowerCase();
        const hasUnclosedItalic =
          lowerCurr.includes("<i") && !lowerCurr.includes("</i>");
        if (idx + 1 < lines.length) {
          const nextL = lines[idx + 1];
          const cleanNext = stripTagsAndBidi(nextL);
          const lowerNext = nextL.toLowerCase();
          const closesItalic =
            lowerNext.includes("</i>") && !lowerNext.includes("<i");
          if (
            DANGLING_CREDIT_REGEX.test(cleanCurr) ||
            (hasUnclosedItalic &&
              closesItalic &&
              cleanNext.length <= 35 &&
              !/[\.?!]/.test(cleanNext))
          ) {
            skipNext = true;
          }
        }
      } else {
        kept.push(l);
      }
    }
    return { kept, removed };
  }

  function detectFileFlipPolarity(content) {
    if (!content) return false;
    let preflippedVotes = 0;
    let logicalVotes = 0;
    const rawLines = content.split(/\r\n|\n|\r/);

    for (const rawLine of rawLines) {
      const s = rawLine
        .replace(/<[^>]+>|\{\\[^}]+\}/g, "")
        .replace(BIDI_CONTROL_CHARS_REGEX, "")
        .trim();
      if (!s || s.includes("-->") || /^\d+$/.test(s)) continue;
      if (!/[\u0590-\u05FF]/.test(s)) continue;

      if (
        /^[\.,!:;]+\s*[\u0590-\u05FF]/.test(s) ||
        /^\?+\s*[\u0590-\u05FF]/.test(s) ||
        /^(?!\.{2,}|…)["'״׳]?[\.?!,:;]+\s*.+(?<![-–—\s][והבלכמש])(?<![-–—])[-–—]$/.test(
          s
        ) ||
        /^[-–—]\s*[\.,?!:;]+/.test(s) ||
        /^[\.,?!:;]+\s*[-–—]/.test(s) ||
        /^["'״׳][\.,?!:;]+[\u0590-\u05FF]/.test(s)
      ) {
        preflippedVotes++;
      } else if (
        /[\u0590-\u05FF]["'״׳\)\]]*[\.?!,:;]+$/.test(s) &&
        !/^[\.?!,:;…]/.test(s)
      ) {
        logicalVotes++;
      }
    }

    return (
      (preflippedVotes >= 2 ||
        (preflippedVotes === 1 && logicalVotes === 0)) &&
      preflippedVotes >= logicalVotes * 0.25
    );
  }

  function canonicalizeVisualFlippedLine(core, isPreflippedFile = false) {
    if (!core || !/[\u0590-\u05FF]/.test(core)) return core;

    let s = core.replace(BIDI_CONTROL_CHARS_REGEX, "").trim();
    if (!s) return core;

    // 1. P_DASH_THEN_PUNCT
    let m = s.match(/^([-–—])\s*([\.?!,:;…]+)\s*(.+?)(?:\s*[-–—])?$/);
    if (m) {
      const [, dash, punct, rawBody] = m;
      const body = rawBody.trim();
      if (!/[\.?!,:;…]$/.test(body)) {
        s = `${dash} ${body}${punct}`;
      }
    }

    // 2. P_PUNCT_THEN_DASH
    m = s.match(/^([\.?!,:;…]+)\s*([-–—])\s*(.+)$/);
    if (m && !/[-–—]$/.test(s)) {
      const [, punct, dash, rawBody] = m;
      const body = rawBody.trim();
      if (!/[\.?!,:;…]$/.test(body)) {
        s = `${dash} ${body}${punct}`;
      }
    }

    // 3. P_FULL_EDGE_SWAP
    m = s.match(
      /^(["'״׳]?\s*(?:\.{2,3}|…|[\.?!,:;]+)\s*["'״׳]?)\s*(.+?)\s*(?<![-–—])([-–—])$/
    );
    if (m) {
      let leadPunct = m[1].trim();
      const body = m[2].trim();
      const dash = m[3];
      const isEllipsisOnly = /^["'״׳\s]*(?:\.{2,3}|…)["'״׳\s]*$/.test(
        leadPunct
      );
      if (isPreflippedFile || !isEllipsisOnly) {
        const mQpEdge = leadPunct.match(/^(["'״׳])(\.{2,3}|…|[\.?!,:;]+)$/);
        if (mQpEdge) {
          leadPunct = mQpEdge[2] + mQpEdge[1];
        }
        s = `${dash} ${body}${leadPunct}`;
      }
    }

    // 4. P_START_QUOTE_PUNCT
    const mQp1 = s.match(
      /^(["'״׳])((?:\.{2,3}|…|[\.?!,:;]+))\s*([\u0590-\u05FF].*)$/
    );
    if (
      mQp1 &&
      (isPreflippedFile || !/^(?:\.{2,3}|…)$/.test(mQp1[2])) &&
      !/[\.?!,:;…]["'״׳]?$/.test(s)
    ) {
      const [, q, punct, rawBody] = mQp1;
      const body = rawBody.trim();
      if (['"', "'", "״", "׳"].some((ch) => body.endsWith(ch))) {
        s = `${q}${body.slice(0, -1)}${punct}${body.slice(-1)}`;
      } else {
        s = `${body}${punct}${q}`;
      }
    } else {
      const mQp2 = s.match(
        /^((?:\.{2,3}|…|[\.?!,:;]+))(["'״׳])\s*([\u0590-\u05FF].*)$/
      );
      if (
        mQp2 &&
        (isPreflippedFile || !/^(?:\.{2,3}|…)$/.test(mQp2[1])) &&
        !/[\.?!,:;…]["'״׳]?$/.test(s)
      ) {
        const [, punct, q, rawBody] = mQp2;
        const body = rawBody.trim();
        if (['"', "'", "״", "׳"].some((ch) => body.endsWith(ch))) {
          s = `${q}${body.slice(0, -1)}${punct}${body.slice(-1)}`;
        } else {
          s = `${body}${punct}${q}`;
        }
      }
    }

    // 5. P_START_PUNCT_NUMBER
    const mNum = s.match(
      /^(?:([,!:;\?]+)|(\.(?!\.)))(\d+)\s+([\u0590-\u05FF].*?)(?:(["'״׳]))?$/
    );
    if (mNum && !/[\.?!,:;…]["'״׳]?$/.test(s)) {
      const punct = mNum[1] || mNum[2];
      const num = mNum[3];
      const body = mNum[4].trim();
      const trailQ = mNum[5] || "";
      s = `${trailQ}${body} ${num}${punct}`;
    }

    // 6. P_START_PUNCT_ATTACHED & P_START_PUNCT_SPACED
    if (!/[\.?!,:;…]["'״׳\)\]]*$/.test(s)) {
      const mAtt = s.match(
        /^(?!\.{2,}|…)([\.?!,:;]+)(?=[\u0590-\u05FF\(\)\[\]"'״׳<])(.*)$/
      );
      if (mAtt) {
        s = `${mAtt[2].trim()}${mAtt[1]}`;
      } else {
        const mSp = s.match(
          /^(?!\.{2,}|…)([,!:;]+|\.(?!\.))\s+([\u0590-\u05FF].*)$/
        );
        if (mSp) {
          s = `${mSp[2].trim()}${mSp[1]}`;
        } else if (isPreflippedFile) {
          const mQm = s.match(/^(\?+)\s+([\u0590-\u05FF].*)$/);
          if (mQm) {
            s = `${mQm[2].trim()}${mQm[1]}`;
          } else {
            const mEl = s.match(/^(\.{2,3}|…)\s*([\u0590-\u05FF].*)$/);
            if (mEl) {
              s = `${mEl[2].trim()}${mEl[1]}`;
            }
          }
        }
      }
    }

    // 7. P_END_DASH_ONLY
    if (isPreflippedFile && !/^[-–—]/.test(s)) {
      const mEd = s.match(
        /^(.+[\u0590-\u05FF][\.?!,:;"'״׳]*)\s*(?<![-–—])([-–—])$/
      );
      if (mEd && !/(?:^|\s)[והבלכמש]$/.test(mEd[1].trim())) {
        s = `${mEd[2]} ${mEd[1].trim()}`;
      }
    }

    // 8. Parentheses & Brackets Canonicalization
    const openParens = (s.match(/\(/g) || []).length;
    const closeParens = (s.match(/\)/g) || []).length;
    if (openParens === 2 && closeParens === 0) {
      const mDop = s.match(/^\(\s*([^\(]+?\s*\([^\(]+?)([\.?!,:;…]*)$/);
      if (mDop) {
        s = `${mDop[1].trim()})${mDop[2]}`;
      } else {
        s = s.replace(/\(([\.?!,:;…]*)$/, ")$1");
      }
    } else if (closeParens === 2 && openParens === 0) {
      const mDcp = s.match(/^\)\s*([^\)]+?)\s*\)\s*([^\)]+?)([\.?!,:;…]*)$/);
      if (mDcp) {
        s = `${mDcp[1].trim()} (${mDcp[2].trim()})${mDcp[3]}`;
      } else if (s.startsWith(")")) {
        s = "(" + s.slice(1);
      }
    } else if (
      openParens === 1 &&
      closeParens === 1 &&
      s.indexOf(")") < s.indexOf("(")
    ) {
      s = s.replace(/\)([^\(\)]+)\(/, "($1)");
    }

    const openBrackets = (s.match(/\[/g) || []).length;
    const closeBrackets = (s.match(/\]/g) || []).length;
    if (openBrackets === 2 && closeBrackets === 0) {
      const mDob = s.match(/^\[\s*([^\[]+?\s*\[[^\[]+?)([\.?!,:;…]*)$/);
      if (mDob) {
        s = `${mDob[1].trim()}]${mDob[2]}`;
      } else {
        s = s.replace(/\[([\.?!,:;…]*)$/, "]$1");
      }
    } else if (closeBrackets === 2 && openBrackets === 0) {
      const mDcb = s.match(/^\]\s*([^\]]+?)\s*\]\s*([^\]]+?)([\.?!,:;…]*)$/);
      if (mDcb) {
        s = `${mDcb[1].trim()} [${mDcb[2].trim()}]${mDcb[3]}`;
      } else if (s.startsWith("]")) {
        s = "[" + s.slice(1);
      }
    } else if (
      openBrackets === 1 &&
      closeBrackets === 1 &&
      s.indexOf("]") < s.indexOf("[")
    ) {
      s = s.replace(/\]([^\[\]]+)\[/, "[$1]");
    }

    return s;
  }

  function applyRlmToLine(
    line,
    isPreflippedFile = false,
    cleanSpeakers = false
  ) {
    line = cleanAndSanitizeText(line);
    let stripped = line.trim();
    if (!stripped) return line;

    if (!/[\u0590-\u05FF]/.test(stripped)) return line;

    stripped = stripped.replace(BIDI_CONTROL_CHARS_REGEX, "");

    let ssaPrefix = "";
    const ssaMatch = stripped.match(/^((?:\{\\[^}]+\})+)\s*(.*)$/);
    if (ssaMatch) {
      ssaPrefix = ssaMatch[1];
      stripped = ssaMatch[2].trim();
    }

    let tagPrefix = "";
    const tagOpenMatch = stripped.match(
      /^((?:<(?:[iIuUbB]|font\b[^>]*)>\s*)+)(.*)$/i
    );
    if (tagOpenMatch) {
      tagPrefix = tagOpenMatch[1];
      stripped = tagOpenMatch[2].trim();
    }

    let tagSuffix = "";
    const tagCloseMatch = stripped.match(
      /((?:\s*<\/(?:[iIuUbB]|font)>)+)$/i
    );
    if (tagCloseMatch) {
      tagSuffix = tagCloseMatch[1];
      stripped = stripped.slice(0, tagCloseMatch.index).trim();
    }

    stripped = canonicalizeVisualFlippedLine(stripped, isPreflippedFile);

    if (!tagPrefix) {
      const postTagOpen = stripped.match(
        /^((?:<(?:[iIuUbB]|font\b[^>]*)>\s*)+)(.*)$/i
      );
      if (postTagOpen) {
        tagPrefix = postTagOpen[1];
        stripped = postTagOpen[2].trim();
      }
    }

    if (cleanSpeakers) {
      stripped = stripped.replace(SPEAKER_TAG_REGEX, "$1").trim();
      if (!stripped) return "";
      if (!/[\u0590-\u05FF]/.test(stripped)) {
        return `${ssaPrefix}${tagPrefix}${stripped}${tagSuffix}`;
      }
    }

    stripped = stripped.replace(
      /([\u0590-\u05FF]{2,})"([\u0590-\u05FF](?:ים|ות|ית)?)(?![\u0590-\u05FF"])(?=\s|$|[\.,?!:;…\)\]\-–—׳'])/g,
      "$1״$2"
    );
    stripped = stripped.replace(
      /(?<![\u0590-\u05FF"])([\u0590-\u05FF])"([\u0590-\u05FF](?:ים|ות)?)(?![\u0590-\u05FF"])(?=\s|$|[\.,?!:;…\)\]\-–—׳'])/g,
      "$1״$2"
    );

    stripped = stripped.replace(
      /(?<![א-ת])(?!(?:ב״ה|ב״ש|ד״ר|ה״י|ה״ש|כ״כ|כ״ע|כ״א|ל״ג|ל״ט|מ״פ|מ״מ|מ״ג|נ״ב|ס״מ|ק״מ|ש״ח|ש״ס|ש״י|ת״א|ז״ל)(?=\s|$|[\.,?!:;…\)\]\-–—]))((?:[והבלכמש]|ו?[בכלהמש]|מה|שה|כש|מש)־?)״([^\s"״][^"״\n]*?(?<=\S))"(?=\s|$|[\.,?!:;…\)\]\-–—])/g,
      '$1"$2"'
    );

    stripped = stripped.replace(/^([-\–\—]\s+)(?=[A-Za-z])/, `$1${RLM}`);
    stripped = stripped.replace(
      /([A-Za-z][A-Za-z0-9\-]*\d|[A-Za-z])([\.!\?,:;…]+)$/,
      `$1${RLM}$2`
    );

    stripped = `${RLM}${stripped}${RLM}`;

    return `${ssaPrefix}${tagPrefix}${stripped}${tagSuffix}`;
  }

  function crossCheckBilingualNumbers(heText, enText) {
    if (!heText || !enText) return heText;
    const enCounts = new Map();
    for (const num of enText.match(/\b\d{2,}\b/g) || []) {
      enCounts.set(num, (enCounts.get(num) || 0) + 1);
    }
    if (enCounts.size === 0) return heText;

    const heVisible = heText.replace(
      /<[^>]+>|&#\d+;|&[A-Za-z0-9#]+;/g,
      " "
    );
    const heCounts = new Map();
    for (const num of heVisible.match(/(?<!\d)\d{2,}(?!\d)/g) || []) {
      heCounts.set(num, (heCounts.get(num) || 0) + 1);
    }

    return heText.replace(
      /(<[^>]+>|&#\d+;)|(?<!\d)(\d{2,})(?!\d)/g,
      function (fullMatch, tagOrEntity, numStr) {
        if (tagOrEntity) return tagOrEntity;
        const revStr = numStr.split("").reverse().join("");
        if (numStr === revStr) {
          return numStr;
        }
        const enRevCount = enCounts.get(revStr) || 0;
        const heRevCount = heCounts.get(revStr) || 0;
        const heNumCount = heCounts.get(numStr) || 0;
        const enNumCount = enCounts.get(numStr) || 0;
        if (enRevCount > heRevCount && heNumCount > enNumCount) {
          heCounts.set(numStr, heNumCount - 1);
          heCounts.set(revStr, heRevCount + 1);
          return revStr;
        }
        return numStr;
      }
    );
  }

  function parseSrtStartMs(timeline) {
    if (!timeline) return null;
    const m = timeline.match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->/);
    if (!m) return null;
    return (
      parseInt(m[1], 10) * 3600000 +
      parseInt(m[2], 10) * 60000 +
      parseInt(m[3], 10) * 1000 +
      parseInt(m[4], 10)
    );
  }

  function parseEnCueMap(enContent) {
    const byIdx = new Map();
    const byTime = new Map();
    const entries = [];
    if (!enContent) return { byIdx, byTime, entries };
    const normalized = enContent.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const blocks = normalized.trim().split(/\n\s*\n/);
    for (const b of blocks) {
      const lines = b.trim().split(/\n/);
      if (lines.length >= 2 && (lines[1].includes("-->") || lines[0].includes("-->"))) {
        const hasIdx = lines[1].includes("-->");
        const idx = hasIdx ? lines[0].trim() : "";
        const time = (hasIdx ? lines[1] : lines[0]).trim();
        const text = (hasIdx ? lines.slice(2) : lines.slice(1)).join("\n");
        if (idx) byIdx.set(idx, text);
        byTime.set(time, text);
        const startMs = parseSrtStartMs(time);
        if (startMs !== null) {
          entries.push({ startMs, text });
        }
      }
    }
    return { byIdx, byTime, entries };
  }

  function findCompanionEnText(enCueMap, timeline) {
    const tKey = timeline.trim();
    if (enCueMap.byTime.has(tKey)) {
      return enCueMap.byTime.get(tKey);
    }
    if (!enCueMap.entries.length) return "";
    const heStartMs = parseSrtStartMs(tKey);
    if (heStartMs === null) return "";
    let bestText = "";
    let bestDiff = 2501;
    for (const entry of enCueMap.entries) {
      const diff = Math.abs(entry.startMs - heStartMs);
      if (diff < bestDiff) {
        bestDiff = diff;
        bestText = entry.text;
      } else if (entry.startMs > heStartMs + 2501) {
        break;
      }
    }
    return bestText;
  }

  function processSrtContent(content, options = {}) {
    const cleanAds = options.cleanAds !== undefined ? options.cleanAds : false;
    const cleanSpeakers =
      options.cleanSpeakers !== undefined ? options.cleanSpeakers : true;
    const enContent = options.enContent || null;

    const normalizedContent = (content || "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n");
    const isPreflippedFile = detectFileFlipPolarity(normalizedContent);
    const enCueMap = parseEnCueMap(enContent);
    const blocks = normalizedContent.trim()
      ? normalizedContent.trim().split(/\n\s*\n/)
      : [];
    const newBlocks = [];
    let totalSubs = 0;
    let modifiedLines = 0;
    let adsRemoved = 0;
    let numbersUnflipped = 0;
    const sampleDiffs = [];

    let idxCounter = 1;

    for (const b of blocks) {
      const lines = b.trim().split(/\n/);
      if (
        lines.length >= 2 &&
        (lines[1].includes("-->") || lines[0].includes("-->"))
      ) {
        const hasIdx = lines[1].includes("-->");
        const timeline = hasIdx ? lines[1] : lines[0];
        const textLines = hasIdx
          ? lines.length >= 3
            ? lines.slice(2)
            : []
          : lines.slice(1);

        const flatText = textLines.join("\n").replace(/\\n/g, "\n");
        let expandedLines = flatText
          .split(/\n/)
          .filter((l) => l.trim().length > 0);
        const wasInitiallyEmpty = expandedLines.length === 0;

        if (cleanAds && !wasInitiallyEmpty) {
          const filtered = filterAdLinesFromBlock(expandedLines);
          expandedLines = filtered.kept;
          adsRemoved += filtered.removed;
          if (expandedLines.length === 0) {
            continue;
          }
        }

        if (wasInitiallyEmpty) {
          totalSubs++;
          const newBlock = [String(idxCounter), timeline, ""];
          idxCounter++;
          newBlocks.push(newBlock.join("\n"));
          continue;
        }

        const newTextLines = [];
        const companionEn = enContent
          ? findCompanionEnText(enCueMap, timeline)
          : "";

        for (let tl of expandedLines) {
          const origTl = tl;
          if (cleanSpeakers) {
            tl = tl.replace(SPEAKER_TAG_REGEX, "$1");
          }
          if (companionEn) {
            const afterNum = crossCheckBilingualNumbers(tl, companionEn);
            if (afterNum !== tl) {
              numbersUnflipped++;
              tl = afterNum;
            }
          }
          const fixed = applyRlmToLine(tl, isPreflippedFile, cleanSpeakers);
          const cleanCheck = fixed.replace(BIDI_CONTROL_CHARS_REGEX, "").trim();
          if (!["", "-", "–", "—"].includes(cleanCheck)) {
            newTextLines.push(fixed);
          }
          if (fixed !== origTl) {
            modifiedLines++;
            const origNoRlm = origTl.replace(BIDI_CONTROL_CHARS_REGEX, "").trim();
            const fixedNoRlm = fixed.replace(BIDI_CONTROL_CHARS_REGEX, "").trim();
            if (sampleDiffs.length < 25) {
              sampleDiffs.push({
                cue: idxCounter,
                timeline,
                before: origNoRlm,
                after: fixed,
                afterNoRlm: fixedNoRlm,
                visualChange: origNoRlm !== fixedNoRlm,
              });
            }
          }
        }

        if (newTextLines.length === 0) {
          continue;
        }

        totalSubs++;
        const newBlock = [String(idxCounter), timeline, ...newTextLines];
        idxCounter++;
        newBlocks.push(newBlock.join("\n"));
      } else if (lines.length > 0 && lines[0].trim()) {
        newBlocks.push(lines.join("\n"));
      }
    }

    const resultText = newBlocks.length > 0 ? newBlocks.join("\n\n") + "\n" : "";
    return {
      resultText,
      totalSubs,
      modifiedLines,
      adsRemoved,
      numbersUnflipped,
      isPreflippedFile,
      sampleDiffs,
    };
  }

  /**
   * Computes a Seed-Safe output filename (`Movie.srt` -> `Movie.he.srt`).
   * Strips control chars / BiDi override characters to prevent spoofing.
   */
  function getSeedSafeFilename(originalName) {
    if (!originalName) return "subtitle.he.srt";
    const safeName = String(originalName)
      .replace(/[\x00-\x1F\x7F\u200E\u200F\u202A-\u202E\u2066-\u2069/\\]/g, "")
      .trim();
    if (!safeName) return "subtitle.he.srt";
    const lower = safeName.toLowerCase();
    if (/\.(?:he|heb)(?:\.(?:sdh|hi|forced))?\.srt$/i.test(lower)) {
      return safeName;
    }
    if (lower.endsWith(".srt")) {
      return safeName.slice(0, -4) + ".he.srt";
    }
    return safeName + ".he.srt";
  }

  return {
    RLM,
    decodeSrtBuffer,
    normalizeFinalLetters,
    cleanAndSanitizeText,
    detectHebrew,
    isAdLine,
    filterAdLinesFromBlock,
    detectFileFlipPolarity,
    canonicalizeVisualFlippedLine,
    applyRlmToLine,
    crossCheckBilingualNumbers,
    processSrtContent,
    getSeedSafeFilename,
  };
});
