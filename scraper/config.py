# === Konfiguration ===
# Deine aktuelle Sleeper League ID (die vom aktuellen Jahr).
LEAGUE_ID = "123456789012345678"  # <- HIER EINTRAGEN!

# Wie viele Wochen pro Saison (Regular Season + ggf. erste Playoff-Runden für volle Wochen-Exports)
MAX_WEEKS = 18  # Sleeper hat idR bis 18 (inkl. BYE-Struktur moderner Saisons)

# Ausgabeverzeichnis (CSV-Dateien landen hier).
OUTPUT_DIR = "output"

# Optional: Stoppe die Rückwärts-Verlinkung bei diesem Jahr (falls sehr alte Saisons fehlerhaft sind)
MIN_YEAR = 2013  # Sleeper ~2017+, aber viele importieren ältere Historien. Passe an, wenn nötig.

# Robustheit: Sekunden zwischen API-Calls (Rate Limit freundlich, 0 = aus)
API_SLEEP = 0.0
