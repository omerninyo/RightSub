# TMDb Metadata & Character Entity Integration

RightSub integrates with **The Movie Database (TMDb)** to provide deterministic, ground-truth metadata resolution for subtitles, character genders, episodic guest stars, genres, and regional dialects.

- **Data Provider**: [The Movie Database (TMDb)](https://www.themoviedb.org)
- **API Reference**: [TMDb API Documentation](https://developer.themoviedb.org/docs)
- *Attribution*: This product uses the TMDb API but is not endorsed or certified by TMDb.

---

## Key Benefits

1. **Deterministic Gender Resolution**: Maps TMDb cast and guest star gender codes (`1=Female`, `2=Male`) to Hebrew pronouns (`את/היא` vs `אתה/הוא`), preventing vocative second-person gender mismatches.
2. **Episodic Guest Stars**: Resolves guest characters (clients, judges, witnesses) per episode.
3. **Context Priming**: Injects plot overview and genre terminology into the AI translation prompt.
4. **Dialect Directives**: Injects British vs American idiom guidance based on `origin_country`.

---

## Setup

```bash
export TMDB_API_KEY="your_api_key_or_bearer_token"
```

If no key is configured, RightSub falls back to local regex extraction gracefully.

---

## Quick CLI Usage

### 1. Standalone Metadata Resolution
```bash
python3 scripts/tmdb_client.py "Boston.Legal.S01E05.1080p.mkv"
```

### 2. Generate Bible with Verified Genders
```bash
./rightsub bible "Boston Legal S01E05.en.srt" --tmdb
```

### 3. Generate Context-Aware Translation Prompts
```bash
./rightsub prompt-gen "Boston Legal S01E05.en.srt" -b translation_bible.json
```
