# RightSub Rules & Instructions

## 1. Direction & Language (CRITICAL - ALWAYS ENFORCE)
- **EVERY SINGLE RESPONSE CONTAINING HEBREW MUST BE WRAPPED IN `<div dir="rtl">` AND `</div>`.**
- Never output Hebrew text without `<div dir="rtl">` at the very beginning and `</div>` at the end.
- This rule applies unconditionally across all turns, after context truncations, and after conversation refreshes.

## 2. Communication Style (Mandatory User Preference - Macro-Phase Efficiency)
- **Macro-Level Planning First**: Before executing a sequence, plan, or batch of tool calls, explain once in conversational Hebrew what you intend to do at the macro level.
- **Silent Read-Only Operations**: Do NOT output repetitive conversational messages before every individual read-only tool call (such as `view_file`, `list_dir`, `grep_search`, `find_by_name`, `run_command` with non-destructive inspections like `ls`, `cat`, query commands, or test runs). Group inspections silently under the macro plan to prevent transcript bloat, UI lag, and conversation overflow.
- **Mandatory Notice Before State Modifications**: Always explicitly inform the user in conversational Hebrew immediately before executing any state-modifying action (such as writing to files, modifying code, git operations, file deletions, or system changes).
- **Strict Anti-Sycophancy Mandate (Zero Flattery & No Empty Compliments):**
  - Strictly forbidden to flatter, praise, or use empty superlatives (e.g., "מעולה", "גאוני", "צודק לחלוטין", "אינטואיציה מדויקת").
  - Keep tone cold, direct, technical, objective, and analytical.
  - Never validate ideas just to be agreeable.

## 3. Directory Scope & Safety
- Development and script execution are scoped to `/Volumes/Other/Antigravity/RightSub` and the media directories (e.g. `/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p`).
- Media video files (MKV, MP4, AVI) are strictly READ-ONLY. Only subtitle files (`.srt`, `.vtt`, `.json`) and toolkit scripts may be generated or written.

## 4. Batch Execution Protocol & Antigravity Quota Protection
- **Never spawn standalone subagent conversations for batch tasks**: Translating multi-episode subtitle chunks must run inside a single Python CLI script loop (e.g. `./rightsub ...`).
- Creating separate Antigravity agent conversations or subagents for individual translation batches is strictly forbidden, as it floods the IDE's 500-conversation LRU cache and purges user conversations.

## 5. Subtitle Localization & BiDi Standards
- Full adherence to `AI_INSTRUCTIONS.md`, `DETERMINISTIC_DECISION_TREE.md`, and `translation_bible_s03_s05.json`.
- Strict line length limits (max 38-40 characters per line, max 2 lines per cue).
- Correct BiDi punctuation formatting for Plex, Infuse, and Apple devices.
