import time
import requests
from .config import API_SLEEP

BASE = "https://api.sleeper.app/v1"

def _get(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    if API_SLEEP:
        time.sleep(API_SLEEP)
    return resp.json()

def league(league_id):
    return _get(f"{BASE}/league/{league_id}")

def league_users(league_id):
    return _get(f"{BASE}/league/{league_id}/users")

def league_rosters(league_id):
    return _get(f"{BASE}/league/{league_id}/rosters")

def league_drafts(league_id):
    return _get(f"{BASE}/league/{league_id}/drafts")

def draft_picks(draft_id):
    return _get(f"{BASE}/draft/{draft_id}/picks")

def matchups(league_id, week):
    return _get(f"{BASE}/league/{league_id}/matchups/{week}")

def players_nfl():
    # ~13–20 MB JSON; wird einmal geladen und wiederverwendet
    return _get(f"{BASE}/players/nfl")

def winners_bracket(league_id):
    # Playoff-Baum (Sieger-Seite) für Playoff-Rankings
    return _get(f"{BASE}/league/{league_id}/winners_bracket")

def losers_bracket(league_id):
    return _get(f"{BASE}/league/{league_id}/losers_bracket")
