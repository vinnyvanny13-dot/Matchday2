"""
Thin wrapper around the API-Football (api-football.com) v3 API.
Free tier: 100 requests/day. We cache aggressively to stay well under that.
Get a free key at https://dashboard.api-football.com/register
"""
import os
import time
import requests

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")

# --- tiny in-memory cache: {key: (timestamp, data)} ---
_cache = {}
CACHE_TTL = 60 * 30  # 30 minutes — fixtures/stats don't change that often


def _get(endpoint: str, params: dict, ttl: int = CACHE_TTL):
    cache_key = f"{endpoint}?{sorted(params.items())}"
    now = time.time()

    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < ttl:
            return data

    if not API_KEY:
        raise RuntimeError(
            "No API_FOOTBALL_KEY set. Get a free key at "
            "https://dashboard.api-football.com/register and set it as an "
            "environment variable."
        )

    headers = {"x-apisports-key": API_KEY}
    resp = requests.get(f"{BASE_URL}/{endpoint}", headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("response", [])
    _cache[cache_key] = (now, data)
    return data


def fixtures_by_date(date: str):
    """date format: YYYY-MM-DD"""
    return _get("fixtures", {"date": date}, ttl=60 * 10)  # shorter TTL, scores change


def search_team(name: str):
    return _get("teams", {"search": name}, ttl=60 * 60 * 24)


def team_last_fixtures(team_id: int, last: int = 10):
    return _get("fixtures", {"team": team_id, "last": last})


def head_to_head(team1_id: int, team2_id: int, last: int = 10):
    return _get("fixtures/headtohead", {"h2h": f"{team1_id}-{team2_id}", "last": last})


def team_info(team_id: int):
    data = _get("teams", {"id": team_id}, ttl=60 * 60 * 24)
    return data[0] if data else None


# ---------------------------------------------------------------------
# Stats derived from a list of fixtures for a single team's perspective
# ---------------------------------------------------------------------
def compute_team_stats(fixtures: list, team_id: int) -> dict:
    """Given a list of fixture objects (from team_last_fixtures) and the
    team's own id, compute form/goal/BTTS/over-under stats."""
    played = wins = draws = losses = 0
    goals_for = goals_against = clean_sheets = btts = over25 = 0
    form_string = []

    # Sort most recent first (API usually returns ascending by date for "last")
    sorted_fx = sorted(fixtures, key=lambda f: f["fixture"]["date"], reverse=True)

    for fx in sorted_fx:
        if fx["fixture"]["status"]["short"] != "FT":
            continue  # skip unfinished/postponed matches

        home = fx["teams"]["home"]
        away = fx["teams"]["away"]
        is_home = home["id"] == team_id

        gf = fx["goals"]["home"] if is_home else fx["goals"]["away"]
        ga = fx["goals"]["away"] if is_home else fx["goals"]["home"]
        if gf is None or ga is None:
            continue

        played += 1
        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1
            form_string.append("W")
        elif gf == ga:
            draws += 1
            form_string.append("D")
        else:
            losses += 1
            form_string.append("L")

        if ga == 0:
            clean_sheets += 1
        if gf > 0 and ga > 0:
            btts += 1
        if (gf + ga) > 2.5:
            over25 += 1

    def pct(n):
        return round(100 * n / played, 1) if played else 0.0

    return {
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "gf_avg": round(goals_for / played, 2) if played else 0,
        "ga_avg": round(goals_against / played, 2) if played else 0,
        "clean_sheet_pct": pct(clean_sheets),
        "btts_pct": pct(btts),
        "over25_pct": pct(over25),
        "form": "".join(form_string[:6]),  # most recent 6, left = most recent
    }
