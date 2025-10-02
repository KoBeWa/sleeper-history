from collections import defaultdict
from .sleeper_api import matchups
from .util import fmt_points, write_csv, ensure_dir, name_from_player, team_abbr, slot_label

# Ziel-Header laut Wunsch
MATCHUP_HEADER = [
    "Owner","Rank",
    "QB","Points","RB","Points","RB","Points","WR","Points","WR","Points","TE","Points","W/R","Points","K","Points","DEF","Points",
    "BN,Points","BN,Points","BN,Points","BN,Points","BN,Points","BN,Points","BN,Points",
    "Total","Opponent","Opponent Total"
]

WANTED_SLOTS = ["QB","RB","RB","WR","WR","TE","W/R","K","DEF"]  # in dieser Reihenfolge

def build_week_rows(league_id, week, rosters_by_id, users_by_id, players):
    """
    Gibt pro Team (Roster) eine Zeile im Ziel-Format zurück.
    """
    entries = matchups(league_id, week)
    if not entries:
        return []

    # Gruppiere Einträge pro matchup_id
    by_matchup = defaultdict(list)
    for e in entries:
        by_matchup[e.get("matchup_id")].append(e)

    # Hilfstabellen
    player_db = players

    # Für Ranking in dieser Woche: erst alle totals berechnen
    rows_tmp = []
    for matchup_id, teams in by_matchup.items():
        # Es sind i.d.R. 2 Teams; bei 3rd place/bye ggf. 1
        for t in teams:
            roster_id = t.get("roster_id")
            roster = rosters_by_id.get(int(roster_id))
            owner_name = roster["owner_display"]
            starters = t.get("starters") or []
            players_points = t.get("players_points") or {}
            total = sum(players_points.get(pid, 0.0) for pid in (t.get("players") or []))

            # Baue Slot-Mapping
            slot_map = {"QB":[], "RB":[], "WR":[], "TE":[], "W/R":[], "K":[], "DEF":[], "BN":[]}
            # Sleeper Startplätze: "FLEX" → W/R (wir mappen alle FLEX zu "W/R")
            # Bench: alle nicht in starters → BN
            starters_set = set(starters)
            all_players = t.get("players") or []

            # Erste Runde: starte mit tatsächlichen Startern (Reihenfolge aus starters)
            for pid in starters:
                p = player_db.get(pid) or {}
                pos = (p.get("position") or "").upper()
                team = team_abbr(p)
                show = f"{name_from_player(p)} {slot_label(pos, team)}".strip()
                pts = fmt_points(players_points.get(pid, 0.0))

                if pos in ("QB","RB","WR","TE","K","DEF"):
                    slot_map[pos].append((show, pts))
                else:
                    # FLEX / SUPERFLEX etc. → W/R
                    slot_map["W/R"].append((show, pts))

            # Zweite Runde: Bench auffüllen (alle, die nicht Starter sind)
            for pid in all_players:
                if pid in starters_set:
                    continue
                p = player_db.get(pid) or {}
                pos = (p.get("position") or "").upper()
                team = team_abbr(p)
                show = f"{name_from_player(p)} {slot_label(pos, team)}".strip()
                pts = fmt_points(players_points.get(pid, 0.0))
                slot_map["BN"].append((show, pts))

            # Gegner + Opponent Total
            opponent_owner = "-"
            opponent_total = "-"
            if len(teams) == 2:
                other = teams[0] if teams[1] == t else teams[1]
                other_roster = rosters_by_id.get(int(other.get("roster_id")))
                opponent_owner = other_roster["owner_display"]
                opp_pts = sum((other.get("players_points") or {}).get(pid, 0.0) for pid in (other.get("players") or []))
                opponent_total = fmt_points(opp_pts)

            rows_tmp.append({
                "owner": owner_name,
                "slot_map": slot_map,
                "total": fmt_points(total),
                "opponent": opponent_owner,
                "opponent_total": opponent_total
            })

    # Weekly Rank nach Total (höchster Score = Rank 1)
    sorted_totals = sorted({float(x["total"]) for x in rows_tmp}, reverse=True)
    def rank_for(total):
        return 1 + sorted_totals.index(float(total))

    # Jetzt Zeilen im Ziel-Format erzeugen
    rows = []
    for r in rows_tmp:
        cells = [r["owner"], rank_for(r["total"])]
        # gewünschte Slots in fester Reihenfolge, bei Bedarf leere Plätze auffüllen
        for slot in WANTED_SLOTS:
            if slot == "RB":
                take = r["slot_map"]["RB"][:2]
                while len(take) < 2:
                    take.append(("-", "0.00"))
                for name, pts in take:
                    cells += [name, pts]
            elif slot == "WR":
                take = r["slot_map"]["WR"][:2]
                while len(take) < 2:
                    take.append(("-", "0.00"))
                for name, pts in take:
                    cells += [name, pts]
            else:
                take = r["slot_map"][slot][:1] if r["slot_map"][slot] else [("-", "0.00")]
                name, pts = take[0]
                cells += [name, pts]

        # Bench (BN) – genau 7 Einträge (falls weniger, auffüllen)
        bench = r["slot_map"]["BN"][:7]
        while len(bench) < 7:
            bench.append(("-", "0.00"))
        for name, pts in bench:
            cells += [f"{name}", f"{pts}"]

        # Total + Opponent
        cells += [r["total"], r["opponent"], r["opponent_total"]]
        rows.append(cells)

    return rows

def export_season_matchups(league_id, season_label, out_dir, rosters_by_id, users_by_id, players):
    all_rows = []
    for wk in range(1, 19):  # 1..18
        rows_w = build_week_rows(league_id, wk, rosters_by_id, users_by_id, players)
        if rows_w:
            all_rows.extend(rows_w)
    if not all_rows:
        return None
    path = f"{out_dir}/matchups_{season_label}.csv"
    write_csv(path, all_rows, MATCHUP_HEADER)
    return path
