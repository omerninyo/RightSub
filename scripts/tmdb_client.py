#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tmdb_client.py
--------------
TMDb (The Movie Database) Metadata & Entity Resolution Engine for RightSub.

Features:
- Smart filename parsing: Extracts title, season, episode, and year from media filenames.
- Clean standard library HTTP client (urllib.request) with Bearer token / API key support.
- Ground-truth gender resolution: Maps TMDb gender enums (1=Female, 2=Male) directly into
  Hebrew grammatical pronouns (את/היא vs אתה/הוא).
- Episodic cast & guest star discovery: Captures one-off characters and clients per episode.
- Production context extraction: Pulls synopsis, origin country, original language, and genres.
- Full Graceful Degradation: Fails cleanly with explanatory messages if no API key is set.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

TMDB_BASE_URL = "https://api.themoviedb.org/3"

def get_tmdb_auth(api_key: str = None) -> tuple:
    """
    Returns (token, is_bearer) from provided key or environment variables:
    TMDB_API_KEY or TMDB_READ_TOKEN.
    """
    key = api_key or os.environ.get("TMDB_API_KEY") or os.environ.get("TMDB_READ_TOKEN")
    if not key:
        return None, False
    key = key.strip()
    # If key starts with 'ey' it is likely a v4 JWT Bearer Read Access Token
    is_bearer = key.startswith("ey") and len(key) > 50
    return key, is_bearer

def is_tmdb_available(api_key: str = None) -> bool:
    """Checks if a valid TMDb token or API key is configured."""
    token, _ = get_tmdb_auth(api_key)
    return token is not None

def tmdb_get(endpoint: str, params: dict = None, api_key: str = None) -> dict:
    """Execute a GET request to TMDb API."""
    token, is_bearer = get_tmdb_auth(api_key)
    if not token:
        raise ValueError("TMDb API key or Read Access Token not found. Set TMDB_API_KEY or TMDB_READ_TOKEN environment variable.")

    params = params or {}
    headers = {
        "Accept": "application/json",
        "User-Agent": "RightSub/2.0 (Subtitle Translation Suite)"
    }

    if is_bearer:
        headers["Authorization"] = f"Bearer {token}"
    else:
        params["api_key"] = token

    url = f"{TMDB_BASE_URL}{endpoint}"
    if params:
        query_str = urllib.parse.urlencode(params)
        url = f"{url}?{query_str}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data
            else:
                return {}
    except urllib.error.HTTPError as err:
        print(f"[-] TMDb HTTP Error {err.code} on {endpoint}: {err.reason}", file=sys.stderr)
        return {}
    except Exception as exc:
        print(f"[-] TMDb Request failed on {endpoint}: {exc}", file=sys.stderr)
        return {}

def parse_media_filename(filepath_or_name: str) -> dict:
    """
    Parses media filenames (e.g. 'Boston.Legal.S01E05.1080p.mkv', 'Inception.2010.mp4')
    into title, season, episode, year, and type.
    """
    raw_name = Path(filepath_or_name).name
    # Strip common subtitle extensions (.he.srt, .en.srt, .srt, .mp4, etc.)
    clean_stem = re.sub(r'(\.(he|en|heb|eng))?\.(srt|vtt|sub|mp4|mkv|m4v|avi|ts)$', '', raw_name, flags=re.IGNORECASE)

    # 1. Look for S01E05 or 1x05 TV pattern
    tv_match = re.search(r'^(.*?)[._\s]+[sS](\d{1,2})[eE](\d{1,3})', clean_stem)
    if not tv_match:
        tv_match = re.search(r'^(.*?)[._\s]+(\d{1,2})x(\d{1,3})', clean_stem)

    if tv_match:
        raw_title = tv_match.group(1)
        season = int(tv_match.group(2))
        episode = int(tv_match.group(3))
        # Clean title dots, underscores and hyphens
        title = re.sub(r'[._]', ' ', raw_title).strip()
        # Clean trailing year in title if present e.g. "Doctor Who 2005"
        year_m = re.search(r'\b(19\d{2}|20\d{2})\b', title)
        year = int(year_m.group(1)) if year_m else None
        if year:
            title = re.sub(rf'\b{year}\b', '', title).strip()
        return {
            "title": title,
            "season": season,
            "episode": episode,
            "year": year,
            "is_tv": True
        }

    # 2. Look for Movie pattern with Year e.g. "Inception.2010.1080p"
    movie_match = re.search(r'^(.*?)[._\s]+[\(\[]?((?:19|20)\d{2})[\)\]]?', clean_stem)
    if movie_match:
        raw_title = movie_match.group(1)
        year = int(movie_match.group(2))
        title = re.sub(r'[._]', ' ', raw_title).strip()
        return {
            "title": title,
            "season": None,
            "episode": None,
            "year": year,
            "is_tv": False
        }

    # 3. Fallback: Clean dots and technical tags
    clean_title = re.sub(r'[._]', ' ', clean_stem)
    clean_title = re.sub(r'\b(1080p|720p|2160p|4k|x264|x265|bluray|web-dl|webrip|hdtv|proper|repack)\b.*$', '', clean_title, flags=re.IGNORECASE).strip()
    return {
        "title": clean_title,
        "season": None,
        "episode": None,
        "year": None,
        "is_tv": None
    }

def map_gender(tmdb_gender_id: int) -> tuple:
    """
    Converts TMDb gender integer code:
    0 = Unknown/Unspecified
    1 = Female
    2 = Male
    3 = Non-binary
    Returns: (gender_str, hebrew_pronouns)
    """
    if tmdb_gender_id == 1:
        return "female", "את/היא"
    elif tmdb_gender_id == 2:
        return "male", "אתה/הוא"
    else:
        return "unknown", "אתה/את"

def search_title(title: str, year: int = None, is_tv: bool = True, api_key: str = None) -> dict:
    """Search for movie or TV show on TMDb."""
    endpoint = "/search/tv" if is_tv else "/search/movie"
    params = {"query": title}
    if year:
        if is_tv:
            params["first_air_date_year"] = year
        else:
            params["year"] = year

    data = tmdb_get(endpoint, params=params, api_key=api_key)
    results = data.get("results", [])
    if not results and is_tv is not None:
        # Fallback retry opposite endpoint if nothing found
        alt_endpoint = "/search/movie" if is_tv else "/search/tv"
        data_alt = tmdb_get(alt_endpoint, params={"query": title}, api_key=api_key)
        results = data_alt.get("results", [])
        if results:
            is_tv = not is_tv

    if not results:
        return None

    best = results[0]
    best["is_tv"] = is_tv
    return best

def fetch_show_or_movie_metadata(
    title: str = None,
    filepath: str = None,
    season: int = None,
    episode: int = None,
    year: int = None,
    api_key: str = None
) -> dict:
    """
    Comprehensive query helper:
    Takes title or filename, queries TMDb, and returns structured metadata,
    cast with 100% verified genders, episodic guest stars, synopsis, and genres.
    """
    if filepath and not title:
        parsed = parse_media_filename(filepath)
        title = parsed["title"]
        season = season or parsed.get("season")
        episode = episode or parsed.get("episode")
        year = year or parsed.get("year")
        is_tv = parsed.get("is_tv", True)
    else:
        is_tv = (season is not None) or True

    if not is_tmdb_available(api_key):
        return {
            "success": False,
            "error": "TMDb API key not configured. Set TMDB_API_KEY environment variable."
        }

    search_res = search_title(title, year=year, is_tv=is_tv, api_key=api_key)
    if not search_res:
        return {
            "success": False,
            "error": f"Title not found on TMDb: '{title}'"
        }

    media_id = search_res["id"]
    is_tv = search_res.get("is_tv", True)
    media_title = search_res.get("name") if is_tv else search_res.get("title")
    overview = search_res.get("overview", "")
    original_lang = search_res.get("original_language", "en")
    origin_country = search_res.get("origin_country", [])

    characters = []
    genre_names = []
    episode_name = None
    episode_overview = None

    if is_tv:
        # 1. Fetch TV Details (Genres)
        tv_details = tmdb_get(f"/tv/{media_id}", api_key=api_key)
        genre_names = [g["name"] for g in tv_details.get("genres", [])]
        if not origin_country and tv_details.get("origin_country"):
            origin_country = tv_details["origin_country"]

        # 2. Fetch Season/Episode Details and Guest Stars
        if season is not None and episode is not None:
            ep_data = tmdb_get(f"/tv/{media_id}/season/{season}/episode/{episode}", api_key=api_key)
            if ep_data:
                episode_name = ep_data.get("name")
                episode_overview = ep_data.get("overview")
                
                # Guest stars for this episode
                for guest in ep_data.get("guest_stars", []):
                    char_name = guest.get("character", "").strip()
                    actor_name = guest.get("name", "").strip()
                    gender_code = guest.get("gender", 0)
                    gender_str, pronouns = map_gender(gender_code)
                    if char_name:
                        characters.append({
                            "name": char_name,
                            "actor": actor_name,
                            "gender": gender_str,
                            "pronouns": pronouns,
                            "is_guest": True
                        })

        # 3. Main Series Cast
        credits_data = tmdb_get(f"/tv/{media_id}/credits", api_key=api_key)
        for c in credits_data.get("cast", []):
            char_name = c.get("character", "").strip()
            actor_name = c.get("name", "").strip()
            gender_code = c.get("gender", 0)
            gender_str, pronouns = map_gender(gender_code)
            if char_name and not any(ch["name"].lower() == char_name.lower() for ch in characters):
                characters.append({
                    "name": char_name,
                    "actor": actor_name,
                    "gender": gender_str,
                    "pronouns": pronouns,
                    "is_guest": False
                })

    else:
        # Movie Credits & Details
        movie_details = tmdb_get(f"/movie/{media_id}", api_key=api_key)
        genre_names = [g["name"] for g in movie_details.get("genres", [])]
        if not origin_country:
            origin_country = [c.get("iso_3166_1", "") for c in movie_details.get("production_countries", [])]
        
        movie_credits = tmdb_get(f"/movie/{media_id}/credits", api_key=api_key)
        for c in movie_credits.get("cast", []):
            char_name = c.get("character", "").strip()
            actor_name = c.get("name", "").strip()
            gender_code = c.get("gender", 0)
            gender_str, pronouns = map_gender(gender_code)
            if char_name:
                characters.append({
                    "name": char_name,
                    "actor": actor_name,
                    "gender": gender_str,
                    "pronouns": pronouns,
                    "is_guest": False
                })

    return {
        "success": True,
        "tmdb_id": media_id,
        "title": media_title,
        "is_tv": is_tv,
        "season": season,
        "episode": episode,
        "episode_name": episode_name,
        "overview": episode_overview or overview,
        "series_overview": overview,
        "original_language": original_lang,
        "origin_country": origin_country,
        "genres": genre_names,
        "characters": characters
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Query TMDb for movie/TV cast, characters, gender, and synopsis.")
    parser.add_argument("target", help="Title (e.g. 'Boston Legal') or video/subtitle filename")
    parser.add_argument("-s", "--season", type=int, help="Season number")
    parser.add_argument("-e", "--episode", type=int, help="Episode number")
    parser.add_argument("-y", "--year", type=int, help="Release year")
    parser.add_argument("--api-key", help="TMDb API key or v4 Bearer Read Token")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    # If target is a file or contains S01E05 pattern
    meta = fetch_show_or_movie_metadata(
        title=args.target if not re.search(r'\.(srt|vtt|mp4|mkv|m4v)$|[sS]\d{1,2}[eE]\d{1,2}', args.target) else None,
        filepath=args.target if re.search(r'\.(srt|vtt|mp4|mkv|m4v)$|[sS]\d{1,2}[eE]\d{1,2}', args.target) else None,
        season=args.season,
        episode=args.episode,
        year=args.year,
        api_key=args.api_key
    )

    if args.json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return

    if not meta.get("success"):
        print(f"[-] Error: {meta.get('error')}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"TMDb Resolution: {meta['title']} (ID: {meta['tmdb_id']})")
    if meta.get("episode"):
        print(f"Episode: S{meta['season']:02d}E{meta['episode']:02d} - {meta.get('episode_name')}")
    print(f"Origin: {meta.get('origin_country')} | Language: {meta.get('original_language')}")
    print(f"Genres: {', '.join(meta.get('genres', []))}")
    print(f"Synopsis: {meta.get('overview', '')[:120]}...")
    print(f"\nCharacters with Verified Gender ({len(meta.get('characters', []))} resolved):")
    for ch in meta.get("characters", [])[:20]:
        guest_tag = " [Guest]" if ch.get("is_guest") else ""
        print(f"  • {ch['name']} ({ch['actor']}){guest_tag}: {ch['gender']} ({ch['pronouns']})")
    print("=" * 60)

if __name__ == "__main__":
    main()
