import os
import csv

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def write_csv(path, rows, header):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def fmt_points(x):
    # Punkte schön mit 2 Nachkommastellen (auch für negative Defense etc.)
    try:
        return f"{float(x):.2f}"
    except:
        return "0.00"

def name_from_player(player):
    # Fallback-Kaskade für Playernamen
    for k in ("full_name", "first_name", "last_name", "search_full_name"):
        if k in player and player[k]:
            if k == "full_name":
                return player[k]
            if k == "search_full_name":
                return player[k].title()
    # Manchmal ist 'first_name' + 'last_name' getrennt
    fn = player.get("first_name") or ""
    ln = player.get("last_name") or ""
    nm = (fn + " " + ln).strip()
    return nm or player.get("display_name") or player.get("player_id") or "Unknown"

def team_abbr(player):
    return player.get("team") or player.get("last_team") or ""

def slot_label(pos, team):
    # Für Ausgabe wie "N. Foles QB - PHI"
    parts = []
    if pos: parts.append(pos)
    if team: parts.append(team)
    if parts:
        return f"{' - '.join(parts)}"
    return ""

def display_or_username(user):
    return user.get("display_name") or user.get("username") or f"user_{user.get('user_id')}"

def teamname_from_roster(roster, users_by_id):
    meta_name = (roster.get("metadata") or {}).get("team_name")
    if meta_name:
        return meta_name
    # fallback: Owner Display Name
    user = users_by_id.get(str(roster.get("owner_id")))
    return display_or_username(user) if user else f"Roster {roster.get('roster_id')}"

def record_str(w, l, t):
    return f"{int(w)}-{int(l)}-{int(t)}"
