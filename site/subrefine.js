/**
 * subrefine.js — RightSub Client-Side SubRefine Mastering Engine (v1.5.0)
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
    /opensubtitles/i,
    /torec(?:\.net)?/i,
    /wizdom(?:\.xyz)?/i,
    /sratim\.co\.il/i,
    /subcenter/i,
    /ktuvit/i,
    /סונכרן\s+(?:על\s+ידי|ע["״']?י)/i,
    /תורגם\s+(?:על\s+ידי|ע["״']?י)/i,
    /^[\u200F\s\-–—]*(?:מלאכת\s+)?ה?תרגום\s*:\s*\S+/i,
    /^[\u200F\s\-–—]*(?:מלאכת\s+)?ה?סנכרון\s*:\s*\S+/i,
    /הורד\s+מ[-–—]/i,
    /הועלה\s+על\s+ידי/i,
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
    [/האחרונ[\u03B5][\u03C2]/g, "האחרונות"],
    [/מב[\u0578]ס[\u03C4][\u03BF][\u03BD]/g, "מבוסטון"],
    [/בא[\u30E1][ר\u30EA][ק\u30AB]ה?/g, "באמריקה"],
    [/לא\s*מ[\u0565\u10D4][ל\u10DA]רוז/g, "לא מלרוז"],
    [/מר\s*מ[\u0995\u09C7\u09AC\u09BE\u0C2C\u0C3E]+/g, "מר מקבה"],
    [/פ[ר\u0F62\u0F0B]+סה/g, "פארסה"],
    [/ג׳ק\s*בוסטי[ק\u0E01\u0E34]+/g, "ג׳ק בוסטיק"],
    [/מתקד[ימ\u056B\u0574]+ם/g, "מתקדימים"],
    [/קרויצפלד[- ]י[א\u10D0][ק\u10D9]וב/g, "קרויצפלד-יאקוב"],
    [/ה[ת\u10D7]זת/g, "התזת"],
    [/(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?ד[\u10D4]ייט(?![א-ת])/g, "$1דייט"],
    [/[\u585A]/g, ""],
    [/\\"/g, '"'],
    [/(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קאבתן(?![א-ת])/g, "$1קברניט"],
    [/(?<![א-ת])לשום\s+את(?![א-ת])/g, "לשים את"],
    [/(?<![א-ת])מוחב\s+אותנו(?![א-ת])/g, "מושכת אותנו"],
  ];

  const DISALLOWED_FOREIGN_SCRIPTS =
    /[\u0600-\u06FF\u0400-\u04FF\u0370-\u03FF\u0530-\u058F\u10A0-\u10FF\u0900-\u0DFF\u0E00-\u0E7F\u0F00-\u0FFF\u3040-\u30FF\u31F0-\u31FF\u4E00-\u9FFF\u3400-\u4DBF\u2E80-\u2EFF\uAC00-\uD7AF]/g;

  const BIDI_CONTROL_CHARS_REGEX = /[\u200e\u200f\u202a-\u202e\u2066-\u2069]/g;

  const SPEAKER_TAG_REGEX =
    /^[\u200F\s]*(?:אלן|דני|שירלי|פול|בראד|לורי|טרה|סאלי|דניס|קייטי|ג'רי|בברלי|אדווין|אישה|גבר|שופט|שופטת|השופט|השופטת|קול|קריין|כולם|גבר 2|אישה 2):\s*/;

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
    const ssaMatch = text.match(/^\s*(\{\\[^}]+\})\s*([\s\S]*)$/);
    if (ssaMatch) {
      ssaLead = ssaMatch[1];
      text = ssaMatch[2];
    }

    text = text.replace(/<truncated\s+\d+\s+bytes>/g, "");

    const hasJsonLeak = /["']?(?:hebrew|index|text)["']?\s*:/.test(text);
    if (hasJsonLeak) {
      text = text.replace(/["']?(?:hebrew|text)["']?\s*:\s*["']?/g, "");
      text = text.replace(/["']?index["']?\s*:\s*\d+,?/g, "");
      text = text.replace(/^\s*[\{\}\[\]]+\s*/g, "");
      text = text.replace(/\s*[\{\}\[\]]+\s*$/g, "");
    } else {
      text = text.replace(/^\s*[\{\}]+\s*/g, "");
      text = text.replace(/\s*[\{\}]+\s*$/g, "");
    }

    text = text.replace(/\\n/g, "\n").replace(/\\r/g, "").replace(/\\"/g, '"');

    for (const [pattern, repl] of UNIVERSAL_PHRASES) {
      text = text.replace(pattern, repl);
    }
    for (const [pattern, repl] of ARABIC_PHRASES) {
      text = text.replace(pattern, repl);
    }

    let hadHomoglyph = false;
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

    text = text.replace(/א\u05B4מ\u05B8?ם/g, "אימם");
    text = text.replace(/(?<=אביהם וגם )אמם(?![א-ת])/g, "אימם");

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

  function isAdLine(line) {
    const clean = line.replace(/<[^>]+>/g, "").trim();
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
        const cleanCurr = l.replace(/<[^>]+>/g, "").trim();
        const lowerCurr = l.toLowerCase();
        const hasUnclosedItalic =
          lowerCurr.includes("<i") && !lowerCurr.includes("</i>");
        if (idx + 1 < lines.length) {
          const nextL = lines[idx + 1];
          const cleanNext = nextL.replace(/<[^>]+>/g, "").trim();
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
    const rawLines = content.split(/\r?\n/);

    for (const rawLine of rawLines) {
      const s = rawLine
        .replace(/<[^>]+>|\{\\[^}]+\}/g, "")
        .replace(BIDI_CONTROL_CHARS_REGEX, "")
        .trim();
      if (!s || s.includes("-->") || /^\d+$/.test(s)) continue;
      if (!/[\u0590-\u05FF]/.test(s)) continue;

      if (
        /^[\.,!:;]+\s*[\u0590-\u05FF]/.test(s) ||
        /^\?+[\u0590-\u05FF]/.test(s) ||
        /^["'״׳]?[\.?!,:;…]+\s*.+[-–—]$/.test(s) ||
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

    return preflippedVotes >= 2 && preflippedVotes >= logicalVotes * 0.25;
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
      /^(["'״׳]?\s*(?:\.{2,3}|…|[\.?!,:;]+)\s*["'״׳]?)\s*(.+?)\s*([-–—])$/
    );
    if (m) {
      let leadPunct = m[1].trim();
      const body = m[2].trim();
      const dash = m[3];
      if (
        leadPunct.length === 2 &&
        '"\'״׳'.includes(leadPunct[0]) &&
        ".?!,:;".includes(leadPunct[1])
      ) {
        leadPunct = leadPunct[1] + leadPunct[0];
      }
      s = `${dash} ${body}${leadPunct}`;
    }

    // 4. P_START_QUOTE_PUNCT
    const mQp1 = s.match(
      /^(["'״׳])((?:\.{2,3}|…|[\.?!,:;]+))\s*([\u0590-\u05FF].*)$/
    );
    if (mQp1 && !/[\.?!,:;…]["'״׳]?$/.test(s)) {
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
      if (mQp2 && !/[\.?!,:;…]["'״׳]?$/.test(s)) {
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
        /^(?!\.{2,}|…)([\.?!,:;]+)(?=[\u0590-\u05FF\(\)\[\]"'״׳])(.*)$/
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
    if (!/^[-–—]/.test(s)) {
      const mEdAttached = s.match(/^(.+[\u0590-\u05FF])([-–—])$/);
      if (mEdAttached) {
        s = `${mEdAttached[2]} ${mEdAttached[1].trim()}`;
      } else if (isPreflippedFile) {
        const mEdSpaced = s.match(
          /^(.+[\u0590-\u05FF][\.?!,:;"'״׳]*)\s+([-–—])$/
        );
        if (mEdSpaced) {
          s = `${mEdSpaced[2]} ${mEdSpaced[1].trim()}`;
        }
      }
    }

    // 8. Parentheses & Brackets Canonicalization
    const openParens = (s.match(/\(/g) || []).length;
    const closeParens = (s.match(/\)/g) || []).length;
    if (openParens === 2 && closeParens === 0) {
      const mDop = s.match(/^\(\s*([^\(]+?\s*\([^\(]+?)([\.?!,:;…]*)$/);
      if (mDop) {
        s = `${mDop[1].trim()})${mDop[2]}`;
      } else if (s.endsWith("(")) {
        s = s.slice(0, -1) + ")";
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
      } else if (s.endsWith("[")) {
        s = s.slice(0, -1) + "]";
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

  function applyRlmToLine(line, isPreflippedFile = false) {
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
    stripped = stripped.replace(/([\u0590-\u05FF])"([\u0590-\u05FF])/g, "$1״$2");
    stripped = stripped.replace(/^([-\–\—]\s+)(?=[A-Za-z])/, `$1${RLM}`);
    stripped = stripped.replace(/(?<=[A-Za-z])([\.!\?,:;…]+)$/, `${RLM}$1`);

    stripped = `${RLM}${stripped}${RLM}`;

    return `${ssaPrefix}${tagPrefix}${stripped}${tagSuffix}`;
  }

  function crossCheckBilingualNumbers(heText, enText) {
    if (!heText || !enText) return heText;
    const enNumbers = new Set(enText.match(/\b\d{2,}\b/g) || []);
    if (enNumbers.size === 0) return heText;

    return heText.replace(/(?<!\d)\d{2,}(?!\d)/g, function (numStr) {
      const revStr = numStr.split("").reverse().join("");
      if (numStr === revStr || enNumbers.has(numStr)) {
        return numStr;
      }
      if (enNumbers.has(revStr)) {
        return revStr;
      }
      return numStr;
    });
  }

  function parseEnCueMap(enContent) {
    const map = new Map();
    if (!enContent) return map;
    const blocks = enContent.trim().split(/\r?\n\s*\r?\n/);
    for (const b of blocks) {
      const lines = b.trim().split(/\r?\n/);
      if (lines.length >= 3) {
        const idx = lines[0].trim();
        const text = lines.slice(2).join("\n");
        map.set(idx, text);
      }
    }
    return map;
  }

  function processSrtContent(content, options = {}) {
    const cleanAds = options.cleanAds !== undefined ? options.cleanAds : false;
    const cleanSpeakers =
      options.cleanSpeakers !== undefined ? options.cleanSpeakers : true;
    const enContent = options.enContent || null;

    const isPreflippedFile = detectFileFlipPolarity(content);
    const enCueMap = parseEnCueMap(enContent);
    const blocks = content.trim() ? content.trim().split(/\r?\n\s*\r?\n/) : [];
    const newBlocks = [];
    let totalSubs = 0;
    let modifiedLines = 0;
    let adsRemoved = 0;
    let numbersUnflipped = 0;
    const sampleDiffs = [];

    let idxCounter = 1;

    for (const b of blocks) {
      const lines = b.trim().split(/\r?\n/);
      if (lines.length >= 2) {
        const origIdx = lines[0].trim();
        const timeline = lines[1];
        const textLines = lines.length >= 3 ? lines.slice(2) : [];

        const flatText = textLines.join("\n").replace(/\\n/g, "\n");
        let expandedLines = flatText
          .split(/\r?\n/)
          .filter((l) => l.trim().length > 0);

        if (cleanAds) {
          const filtered = filterAdLinesFromBlock(expandedLines);
          expandedLines = filtered.kept;
          adsRemoved += filtered.removed;
          if (expandedLines.length === 0) {
            continue;
          }
        }

        totalSubs++;
        const newTextLines = [];
        const companionEn = enCueMap.get(origIdx) || "";

        for (let tl of expandedLines) {
          const origTl = tl;
          if (cleanSpeakers) {
            tl = tl.replace(SPEAKER_TAG_REGEX, "");
          }
          if (companionEn) {
            const afterNum = crossCheckBilingualNumbers(tl, companionEn);
            if (afterNum !== tl) {
              numbersUnflipped++;
              tl = afterNum;
            }
          }
          const fixed = applyRlmToLine(tl, isPreflippedFile);
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
                after: fixedNoRlm,
                visualChange: origNoRlm !== fixedNoRlm,
              });
            }
          }
        }

        if (newTextLines.length === 0) {
          continue;
        }

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
   */
  function getSeedSafeFilename(originalName) {
    if (!originalName) return "subtitle.he.srt";
    const lower = originalName.toLowerCase();
    if (lower.endsWith(".he.srt") || lower.endsWith(".heb.srt")) {
      return originalName;
    }
    if (lower.endsWith(".srt")) {
      return originalName.slice(0, -4) + ".he.srt";
    }
    return originalName + ".he.srt";
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
