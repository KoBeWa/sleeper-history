# Sleeper League History Scraper

Scraped die komplette History einer Sleeper Fantasy-Football-Liga und exportiert:
1) Wöchentliche Matchups pro Saison (`output/matchups_YYYY.csv`)
2) Saison-Standings (`output/standings_<league_id>.csv`)

## Setup

1. `scraper/config.py` öffnen und `LEAGUE_ID` eintragen.
2. (Optional) `MIN_YEAR` anpassen.
3. Lokal testen:
   ```bash
   pip install -r requirements.txt
   python main.py
