# TMDb Metadata & Character Entity Integration

RightSub integrates with **The Movie Database (TMDb)** to provide deterministic, ground-truth metadata resolution for subtitles, character genders, episodic guest stars, genres, and regional dialects.

- **Data Provider**: [The Movie Database (TMDb)](https://www.themoviedb.org)
- **API Reference**: [TMDb API v3/v4 Documentation](https://developer.themoviedb.org/docs)
- *Attribution Notice*: This product uses the TMDb API but is not endorsed or certified by TMDb.

---

## 🎯 Problems Solved

1. **Deterministic Gender Resolution (Zero Guesswork)**:
   - In Hebrew, second-person direct address ("אתה" vs "את") and verb conjugations strictly depend on gender.
   - While main characters are well known, episodic guest characters (e.g. witnesses, clients, opposing counsel, judges) change every episode and often carry unisex names (Terry, Jordan, Robin, Pat, Dr. Adams).
   - TMDb provides an explicit `gender` enum for every cast member and episodic guest star (`1 = Female`, `2 = Male`), mapping directly to Hebrew pronouns (`את/היא` vs `אתה/הוא`).

2. **Episodic Plot Synopsis & Context Priming**:
   - Fetches the exact episode summary (`overview`) and title.
   - Primes the AI translation prompt in `09_prompt_builder.py`, giving the LLM deep narrative context to disambiguate polysemous words (e.g. legal "case", "brief", "damages").

3. **Linguistic Dialect & Cultural Register Directives**:
   - Detects `origin_country` and `original_language` (e.g. `GB` for United Kingdom).
   - Automatically injects dialect guidelines into translation prompts for British English vs American English idioms (`pissed`, `mate`, `cheers`, `pants`, `rubber`).
   - Extracts genres (e.g. *Legal*, *Medical*, *Sci-Fi*) to enforce professional terminology.

---

## ⚙️ Setup & Configuration

TMDb provides free API access for personal and developer use:

1. Create a free account at [themoviedb.org](https://www.themoviedb.org/signup).
2. Go to **Settings > API** to generate your API Key (v3) or API Read Access Token (v4).
3. Set the key in your terminal environment:
   ```bash
   export TMDB_API_KEY="your_api_key_or_bearer_token"
   ```
   *(You can also add this line to your `~/.zshrc` or `~/.bashrc`)*.

### Graceful Fallback
If `TMDB_API_KEY` is not configured, RightSub automatically falls back to local regex heuristics from your SRT files without raising errors.

---

## 🚀 Usage & Commands

### 1. Standalone Metadata Resolution
Inspect media metadata and resolved character genders directly:
```bash
python3 scripts/tmdb_client.py "Boston.Legal.S01E05.1080p.mkv"
```
Or query by title, season, and episode:
```bash
python3 scripts/tmdb_client.py "Boston Legal" -s 1 -e 5
```

### 2. Generate Translation Bible with Verified Genders
Extract local SRT speakers and enrich them with TMDb ground-truth cast and guest stars:
```bash
python3 scripts/03_generate_bible.py "Boston Legal S01E05.en.srt" --tmdb -o translation_bible.json
```
Or via the `rightsub` CLI:
```bash
./rightsub bible "Boston Legal S01E05.en.srt" --tmdb
```

### 3. Automatic Prompt Context Priming
When `09_prompt_builder.py` runs, it reads the enriched `translation_bible.json`:
- Injects verified character genders into the Character Roster.
- Injects the episode synopsis into the Extra Context block.
- Adds dialect directives if non-US/British origins are detected.
```bash
./rightsub prompt-gen "Boston Legal S01E05.en.srt" -b translation_bible.json
```
