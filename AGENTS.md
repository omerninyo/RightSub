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
- Full adherence to `AI_INSTRUCTIONS.md`, `DETERMINISTIC_DECISION_TREE.md`, and generated `translation_bible.json`.
- Strict line length limits (max 38-40 characters per line, max 2 lines per cue).
- Correct BiDi punctuation formatting for Plex, Infuse, and Apple devices.

## 6. Value-Driven Release Notes Protocol (Zero Alert Fatigue)
- Release notes (`docs/WHATS_NEW.md`, `docs/WHATS_NEW.he.md`, and GitHub Releases) are strictly reserved for **major milestone releases** (new core capabilities, cross-platform parity, architectural breakthroughs).
- **Strictly forbidden to publish release notes for routine changes**: Minor bug fixes, code refactoring, typo corrections, or incremental tests remain solely in standard git commits and technical changelogs to avoid alert fatigue.
- Each milestone entry must follow the 4-part value structure: Highlights / TL;DR, Why It Matters, Quick Upgrade / Getting Started, and Deep Dive Links.
- Releases in GitHub should use `.github/release_template.md`.

## 7. Continuous Product Roadmap & GitHub Issue Governance Protocol
- **MANDATORY 5-STEP FEATURE LIFECYCLE (Zero Ideas Lost, 100% Tracking)**:
  Whenever a new feature, architecture idea, or user enhancement request is discussed, approved, or proposed, the AI assistant MUST unconditionally execute this standardized sequence:
  1. **Technical Specification (RFC)**:
     - Author a formal bilingual RFC document under `docs/proposals/RFC_XXX_<TITLE>.he.md` and `docs/proposals/RFC_XXX_<TITLE>.md`.
     - Never create floating, unorganized `FUTURE_*.md` files.
  2. **GitHub Issue & Milestone Tracking**:
     - Create an official GitHub Issue using the `github` MCP tool (`create_issue`) with the label `enhancement` and assign it to the appropriate GitHub Milestone (e.g. `v1.4.0`, `v1.5.0`).
     - Standard title format: `feat(<scope>): <Description> (RFC XXX)`.
  3. **Roadmap Binding**:
     - Log the feature under the target release section in `ROADMAP.he.md` and `ROADMAP.md`.
     - Explicitly hyperlink both the RFC document and the GitHub Issue: `- [ ] **<Title>** ([#X](https://github.com/omerninyo/RightSub/issues/X)): ...`.
  4. **Bilingual Wiki Synchronization**:
     - Create the corresponding wiki page under `wiki/` (e.g. `wiki/<RFC-Title>.md`).
     - Add the entry to both language sections of `wiki/_Sidebar.md`.
     - Execute `python3 scripts/sync_wiki.py` to push changes to `RightSub.wiki.git`.
  5. **Implementation, Verification & Closure (Definition of Done)**:
     - A feature, integration, or CLI command is strictly NEVER considered "Done" without:
       a. Complete unit and integration test coverage in `tests/` with 100% passing test suite.
       b. CLI command reference table updated in both `README.md` and `README.he.md` (validated by `test_docs_consistency.py`).
       c. Corresponding operational guide updated or created under `docs/` (e.g. `INTEGRATIONS_GUIDE`, `AI_INSTRUCTIONS`).
       d. Bidirectional GitHub Wiki synchronization executed via `python3 scripts/sync_wiki.py`.
       e. Git commit message containing `closes #X` to automatically close the tracking issue, link commits, and advance milestone progress.
     - Move the feature from "Planned" to "Shipped" in `ROADMAP.he.md` and `ROADMAP.md`, and document in `WHATS_NEW` for major milestone releases.
- **Strict Issue Taxonomy**:
  - `enhancement` (light blue): Feature requests, architecture expansions, and RFC tasks.
  - `bug` (red): Runtime defects or regression errors.
  - No new feature idea or user request may remain solely in conversation context; it must immediately be codified into the project's tracked lifecycle.

## 8. Core Engineering Invariants & Resource Discipline
1. **Zero-Heavy-Dependency Servers & Daemons**:
   - Webhook listeners, event daemons, and background servers must be built exclusively using Python standard library modules (`http.server.ThreadingHTTPServer` or `asyncio`).
   - Heavy web frameworks (Flask, FastAPI, Django, Tornado) are strictly prohibited for internal listeners to maintain an idle memory footprint of <15 MB RAM and keep Docker images slim.
   - Any server receiving payloads from containerized environments (Sonarr, Radarr, Bazarr) MUST provide native cross-container path translation via `PATH_MAP`.
2. **Seed-Safe by Default & Media Player Acceleration**:
   - Automation pipelines and listeners must never modify original torrent download files in-place if doing so risks altering file hashes and breaking active seeding. Always produce companion sidecar `.he.srt` files by default.
   - Any script or daemon modifying or generating subtitle files must touch the file's access and modification timestamps (`os.utime(target, None)`) to force immediate index detection by Plex and Infuse without requiring library rescans.
3. **Source-Audited Competitive Analysis**:
   - Comparative claims against external or competing tools (e.g. Bazarr, Subtitle Edit, Whisper, Plex) in technical documentation or RFCs must be verified directly against the target project's upstream source code or official technical documentation.
   - Hand-waving assertions, unverified assumptions, or promotional exaggeration are strictly prohibited.


