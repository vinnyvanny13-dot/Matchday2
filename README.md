# Matchsheet

A personal football-analysis web app: browse fixtures, look up a team's
recent form, and compare two teams head-to-head (goals, clean sheets,
BTTS%, over/under trends). Built with Flask, styled like a printed
matchday programme rather than a generic SaaS dashboard.

## 1. Get a free API key

Sign up at **https://dashboard.api-football.com/register** (free tier =
100 requests/day, which is plenty for personal use since this app caches
responses for 10–30 minutes). Copy your key from the dashboard.

## 2. Run it locally

```bash
cd footy-analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

export API_FOOTBALL_KEY=your_key_here   # Windows: set API_FOOTBALL_KEY=...
python app.py
```

Visit http://localhost:5000

## 3. Deploy to Render (free tier)

1. Push this folder to a GitHub repo.
2. On [render.com](https://render.com), click **New → Web Service** and
   connect the repo.
3. Render should auto-detect Python. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app` (already in the `Procfile`,
     Render picks it up automatically)
4. Under **Environment**, add:
   - `API_FOOTBALL_KEY` = your key
5. Deploy. Render free web services spin down after inactivity and take
   ~30–50s to wake back up on the next visit — normal for the free tier.

## How it's built

- `app.py` — Flask routes (fixtures by date, team search, team profile,
  head-to-head comparison)
- `api_client.py` — all API-Football calls + an in-memory cache (so
  repeated views of the same day/team don't burn your daily quota) + the
  stat math (form, goals/game, clean sheet %, BTTS %, over 2.5 %)
- `templates/` — Jinja templates
- `static/style.css` — the visual design

## Extending it

Ideas if you want to keep building:
- Swap the in-memory cache for SQLite so data survives a restart (Render's
  free filesystem is ephemeral, so pair with a scheduled re-fetch, or use
  Render's free Postgres tier)
- Add a "today's best matches" scoring heuristic on the fixtures page
  using the same stats already computed on the team pages
- Add league-table standings (`/standings?league=...&season=...` endpoint
  on API-Football)
- Add odds comparison via the API's `/odds` endpoint if useful to you
