from datetime import date
from flask import Flask, render_template, request

import api_client as api

app = Flask(__name__)


@app.route("/")
def index():
    selected_date = request.args.get("date") or date.today().isoformat()
    error = None
    fixtures = []
    try:
        raw = api.fixtures_by_date(selected_date)
        # Keep it light: only send the template what it needs
        for fx in raw:
            fixtures.append({
                "id": fx["fixture"]["id"],
                "date": fx["fixture"]["date"],
                "status": fx["fixture"]["status"]["short"],
                "league": fx["league"]["name"],
                "league_logo": fx["league"]["logo"],
                "home": fx["teams"]["home"]["name"],
                "home_id": fx["teams"]["home"]["id"],
                "home_logo": fx["teams"]["home"]["logo"],
                "away": fx["teams"]["away"]["name"],
                "away_id": fx["teams"]["away"]["id"],
                "away_logo": fx["teams"]["away"]["logo"],
                "goals_home": fx["goals"]["home"],
                "goals_away": fx["goals"]["away"],
            })
        # group by league for a cleaner sheet
        fixtures.sort(key=lambda f: (f["league"], f["date"]))
    except Exception as e:
        error = str(e)

    return render_template("index.html", fixtures=fixtures, selected_date=selected_date, error=error)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    error = None
    if query:
        try:
            raw = api.search_team(query)
            results = [{
                "id": t["team"]["id"],
                "name": t["team"]["name"],
                "logo": t["team"]["logo"],
                "country": t["team"]["country"],
            } for t in raw]
        except Exception as e:
            error = str(e)
    return render_template("search.html", query=query, results=results, error=error)


@app.route("/team/<int:team_id>")
def team_page(team_id):
    error = None
    info = None
    stats = None
    fixtures = []
    try:
        info = api.team_info(team_id)
        raw_fixtures = api.team_last_fixtures(team_id, last=10)
        stats = api.compute_team_stats(raw_fixtures, team_id)
        for fx in sorted(raw_fixtures, key=lambda f: f["fixture"]["date"], reverse=True):
            fixtures.append({
                "date": fx["fixture"]["date"][:10],
                "home": fx["teams"]["home"]["name"],
                "away": fx["teams"]["away"]["name"],
                "goals_home": fx["goals"]["home"],
                "goals_away": fx["goals"]["away"],
                "status": fx["fixture"]["status"]["short"],
            })
    except Exception as e:
        error = str(e)

    return render_template("team.html", info=info, stats=stats, fixtures=fixtures, error=error)


@app.route("/compare")
def compare():
    team1_id = request.args.get("team1", type=int)
    team2_id = request.args.get("team2", type=int)
    error = None
    team1 = team2 = None
    h2h_summary = None

    if team1_id and team2_id:
        try:
            info1 = api.team_info(team1_id)
            info2 = api.team_info(team2_id)
            fx1 = api.team_last_fixtures(team1_id, last=10)
            fx2 = api.team_last_fixtures(team2_id, last=10)
            team1 = {"info": info1, "stats": api.compute_team_stats(fx1, team1_id)}
            team2 = {"info": info2, "stats": api.compute_team_stats(fx2, team2_id)}

            h2h_raw = api.head_to_head(team1_id, team2_id, last=10)
            wins1 = wins2 = draws = 0
            for fx in h2h_raw:
                if fx["fixture"]["status"]["short"] != "FT":
                    continue
                gh, ga = fx["goals"]["home"], fx["goals"]["away"]
                if gh is None or ga is None:
                    continue
                home_id = fx["teams"]["home"]["id"]
                if gh == ga:
                    draws += 1
                elif (gh > ga and home_id == team1_id) or (ga > gh and home_id != team1_id):
                    wins1 += 1
                else:
                    wins2 += 1
            h2h_summary = {"wins1": wins1, "wins2": wins2, "draws": draws, "played": len(h2h_raw)}
        except Exception as e:
            error = str(e)

    return render_template(
        "compare.html", team1=team1, team2=team2, h2h=h2h_summary,
        team1_id=team1_id, team2_id=team2_id, error=error
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
