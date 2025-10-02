from collections import defaultdict
from .sleeper_api import league_rosters, league_users, league_drafts, winners_bracket
from .util import write_csv, display_or_username, teamname_from_roster, record_str, fmt_points

HEADER_STANDINGS = [
    "TeamName","RegularSeasonRank","Record","PointsFor","PointsAgainst","PlayoffRank","ManagerName","Moves","Trades","DraftPosition"
]

def _regular_season_rank(rosters):
    # Sortiere nach Wins, dann PointsFor (descending). Ties, Losses werden implizit berücksichtigt.
    # rosters: list of dict with 'wins','losses','ties','fpts'
    sorted_rs = sorted(
        rosters,
        key=lambda r: (
            -int(r["settings"].get("wins",0)),
            float(r["settings"].get("fpts",0)) + float(r["settings"].get("fpts_decimal",0))/1000.0
        )
    )
    rank_map = {r["roster_id"]: i+1 for i, r in enumerate(sorted_rs)}
    return rank_map

def _playoff_ranks_from_bracket(wb):
    """
    winners_bracket liefert Matches mit 'r' (runde), 't1','t2','w' (winner roster_id), 'l' (loser roster_id) etc.
    Wir leiten daraus finale Platzierungen ab:
      - Gewinner des Finales = 1
      - Verlierer des Finales = 2
      - Gewinner 3rd-place = 3, Verlierer = 4
      - Rest nach Ausscheiderunde ungefähr (nicht perfekt, aber gängig)
    """
    if not wb:
        return {}
    # Finde Finalspiele (höchste Runde mit 'p': 'championship' o.ä. kommt vor, aber nicht zuverlässig)
    max_round = max((m.get("r",0) for m in wb), default=0)
    finals = [m for m in wb if m.get("r",0) == max_round]
    playoff_rank = {}

    # Versuche Final (championship) zu identifizieren: in der letzten Runde gibt es oft 1 Match
    if finals:
        fin = finals[0]
        w = fin.get("w")
        l = fin.get("l")
        if w: playoff_rank[w] = 1
        if l: playoff_rank[l] = 2

    # 3rd place (vorletzte Runde zwischen den Halbfinal-Verlierern):
    # Heuristik: Runde max_round hat 1 Match (Finale), Runde max_round hat evtl. zweites Match (3rd)
    # Falls vorhanden:
    if len(finals) > 1:
        third = finals[1]
        w3 = third.get("w")
        l3 = third.get("l")
        if w3: playoff_rank[w3] = 3
        if l3: playoff_rank[l3] = 4

    # Für alle übrigen Teams: falls nicht gesetzt, grob nach Ausscheiderunde rangieren
    # (Optional, einfache Heuristik — kann je Liga leicht variieren)
    knocked_round = {}
    for m in wb:
        loser = m.get("l")
        rnd = m.get("r",0)
        if loser:
            knocked_round[loser] = max(knocked_round.get(loser,0), rnd)

    # Teams, die keinen Rank haben, nach späterem Ausscheiden besser einstufen
    remaining = [rid for rid in set(list(knocked_round.keys())) if rid not in playoff_rank]
    remaining_sorted = sorted(remaining, key=lambda rid: -knocked_round[rid])
    next_rank = max(playoff_rank.values(), default=0) + 1
    for rid in remaining_sorted:
        if rid not in playoff_rank:
            playoff_rank[rid] = next_rank
            next_rank += 1

    return playoff_rank

def export_season_standings(league_id, out_dir):
    users = league_users(league_id)
    users_by_id = {str(u["user_id"]): u for u in users}
    rosters = league_rosters(league_id)
    rosters_by_id = {int(r["roster_id"]): r for r in rosters}

    # Draftposition via /drafts
    drafts = league_drafts(league_id) or []
    draft_pos = {}
    if drafts:
        # Nimm den ersten Draft der Saison
        d = drafts[0]
        draft_order = (d.get("draft_order") or {})
        for uid, slot in draft_order.items():
            # draft_order mappt user_id → slot; wir brauchen roster_id → slot
            # Finde roster dieses users:
            for rid, r in rosters_by_id.items():
                if str(r.get("owner_id")) == str(uid):
                    draft_pos[rid] = slot

    # Regular Season Rank
    rs_rank = _regular_season_rank(rosters)

    # Playoff Rank (falls Bracket verfügbar)
    wb = winners_bracket(league_id)
    pr_rank = _playoff_ranks_from_bracket(wb)

    rows = []
    for rid, r in rosters_by_id.items():
        team_name = teamname_from_roster(r, users_by_id)
        owner = users_by_id.get(str(r.get("owner_id")), {})
        manager_name = (owner.get("metadata") or {}).get("team_name") or owner.get("display_name") or owner.get("username")

        st = r.get("settings") or {}
        wins = st.get("wins", 0)
        losses = st.get("losses", 0)
        ties = st.get("ties", 0)
        fpts = float(st.get("fpts", 0)) + float(st.get("fpts_decimal", 0))/1000.0
        fpta = float(st.get("fpts_against", 0)) + float(st.get("fpts_against_decimal", 0))/1000.0

        moves = r.get("metadata", {}).get("waiver_moves") or r.get("moves", 0)  # je nach Saison/Import
        trades = r.get("metadata", {}).get("trades") or r.get("total_trades", 0)

        row = [
            team_name,
            rs_rank.get(rid, ""),                      # RegularSeasonRank
            record_str(wins, losses, ties),           # Record
            f"{fpts:.2f}",                            # PointsFor
            f"{fpta:.2f}",                            # PointsAgainst
            pr_rank.get(rid, ""),                     # PlayoffRank (leer wenn keine Playoffs)
            manager_name,
            moves if isinstance(moves, int) else 0,
            trades if isinstance(trades, int) else 0,
            draft_pos.get(rid, "")                    # DraftPosition
        ]
        rows.append(row)

    # Sortiert nach RegularSeasonRank
    rows.sort(key=lambda x: (999 if x[1]=="" else int(x[1])))
    from .util import write_csv
    path = f"{out_dir}/standings_{league_id}.csv"
    write_csv(path, rows, HEADER_STANDINGS)
    return path
