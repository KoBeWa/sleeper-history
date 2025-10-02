import os
from scraper.config import LEAGUE_ID, OUTPUT_DIR, MIN_YEAR
from scraper.sleeper_api import league, league_rosters, league_users, players_nfl
from scraper.build_matchups import export_season_matchups
from scraper.build_standings import export_season_standings
from scraper.util import ensure_dir, display_or_username

def walk_back_leagues(start_league_id):
    """
    Läuft über die 'previous_league_id'-Kette zurück und liefert [(league_id, season_label), ...]
    """
    chain = []
    curr = start_league_id
    seen = set()
    while curr and curr not in seen:
        seen.add(curr)
        lg = league(curr)
        season = lg.get("season")
        season_label = str(season) if season else curr
        try:
            if season and int(season) < MIN_YEAR:
                chain.append((curr, season_label))
                break
        except:
            pass
        chain.append((curr, season_label))
        curr = lg.get("previous_league_id")
    return chain  # vom neuesten nach hinten

def prepare_roster_user_maps(league_id):
    us = league_users(league_id)
    rs = league_rosters(league_id)
    users_by_id = {str(u["user_id"]): u for u in us}

    rosters_by_id = {}
    for r in rs:
        rid = int(r["roster_id"])
        owner_id = str(r.get("owner_id"))
        owner = users_by_id.get(owner_id)
        owner_display = display_or_username(owner) if owner else f"Owner {owner_id}"
        r["owner_display"] = owner_display
        rosters_by_id[rid] = r
    return rosters_by_id, users_by_id

def main():
    ensure_dir(OUTPUT_DIR)
    # Einmal Player-DB laden (groß, aber lohnt sich)
    players = players_nfl()

    # Alle Saisons rückwärts ablaufen
    chain = walk_back_leagues(LEAGUE_ID)

    for lg_id, season_label in chain:
        print(f"==> Verarbeite Saison {season_label} (League {lg_id})")

        # Roster/User-Mapping
        rosters_by_id, users_by_id = prepare_roster_user_maps(lg_id)

        # Matchups exportieren
        m_path = export_season_matchups(lg_id, season_label, OUTPUT_DIR, rosters_by_id, users_by_id, players)
        if m_path:
            print(f"   Matchups -> {m_path}")
        else:
            print(f"   Keine Matchups gefunden.")

        # Standings exportieren
        s_path = export_season_standings(lg_id, OUTPUT_DIR)
        print(f"   Standings -> {s_path}")

if __name__ == "__main__":
    main()
