from datetime import date

# Bond tickers and their expiration dates
TICKERS = {
    "S16A5": date(2025, 4, 16),
    "S28A5": date(2025, 4, 28),
    "S16Y5": date(2025, 5, 16),
    "S30Y5": date(2025, 5, 30),
    "S18J5": date(2025, 6, 18),
    "S30J5": date(2025, 6, 30),
    "S31L5": date(2025, 7, 31),
    "S15G5": date(2025, 8, 15),
    "S29G5": date(2025, 8, 29),
    "S12S5": date(2025, 9, 12),
    "S30S5": date(2025, 9, 30),
    "T17O5": date(2025, 10, 15),
    "S31O5": date(2025, 10, 31),
    "S10N5": date(2025, 11, 10),
    "S28N5": date(2025, 11, 28),
    "T15D5": date(2025, 12, 15),
    "S16E6": date(2026, 1, 16),
    "T30E6": date(2026, 1, 30),
    "T13F6": date(2026, 2, 13),
    "S27F6": date(2026, 2, 27),
    "S17A6": date(2026, 4, 17),
    "S30A6": date(2026, 4, 30),
    "S29Y6": date(2026, 5, 29),
    "T30J6": date(2026, 6, 30),
    "S31G6": date(2026, 8, 31),
    "S30O6": date(2026, 10, 30),
    "S30N6": date(2026, 11, 30),
    "T15E7": date(2027, 1, 15),
    "T30A7": date(2027, 4, 30),
    "T31Y7": date(2027, 5, 31),
    "TTM26": date(2026, 3, 16),
    "TTJ26": date(2026, 6, 30),
    "TTS26": date(2026, 9, 15),
    "TTD26": date(2026, 12, 15),
}

# Bond payoff values
PAYOFF = {
    "S16A5": 131.211,
    "S28A5": 130.813,
    "S16Y5": 136.861,
    "S30Y5": 136.331,
    "S18J5": 147.695,
    "S30J5": 146.607,
    "S31L5": 147.74,
    "S15G5": 146.794,
    "S29G5": 157.7,
    "S12S5": 158.977,
    "S30S5": 159.734,
    "T17O5": 158.872,
    "S31O5": 132.821,
    "S10N5": 122.254,
    "S28N5": 123.561,
    "T15D5": 170.838,
    "S16E6": 119.06,
    "T30E6": 142.22,
    "T13F6": 144.97,
    "S27F6": 125.84,
    "S17A6": 109.94,
    "S30A6": 127.49,
    "S29Y6": 132.04,
    "T30J6": 144.90,
    "S31G6": 127.06,
    "S30O6": 135.28,
    "S30N6": 129.89,
    "T15E7": 160.18,
    "T30A7": 157.13,
    "T31Y7": 152.18,
    "TTM26": 135.238,
    "TTJ26": 144.629,
    "TTS26": 152.096,
    "TTD26": 161.144,
}

# API endpoints
DATA912_BASE_URL = "https://data912.com/live"
MEP_ENDPOINT = f"{DATA912_BASE_URL}/mep"
NOTES_ENDPOINT = f"{DATA912_BASE_URL}/arg_notes"
BONDS_ENDPOINT = f"{DATA912_BASE_URL}/arg_bonds"

# Currency band parameters
BAND_BASE_VALUE = 1400
BAND_MONTHLY_RATE = 0.01
BAND_START_DATE = date(2025, 4, 14)

# Carry trade scenarios
CARRY_SCENARIOS = [1000, 1100, 1200, 1300, 1400]