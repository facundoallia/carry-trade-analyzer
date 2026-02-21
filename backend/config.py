from datetime import date

# Bond tickers and their expiration dates
TICKERS = {
    "T17O5": date(2025, 10, 17),
    "S31O5": date(2025, 10, 31),
    "S10N5": date(2025, 11, 10),
    "S28N5": date(2025, 11, 28),
    "T15D5": date(2025, 12, 15),
    "S16E6": date(2026, 1, 16),
    "T30E6": date(2026, 1, 30),
    "T13F6": date(2026, 2, 13),
    "S27F6": date(2026, 2, 27),
    "S16M6": date(2026, 3, 16),
    "TTM26": date(2026, 3, 16),
    "S17A6": date(2026, 4, 17),
    "S30A6": date(2026, 4, 30),
    "S29Y6": date(2026, 5, 29),
    "T30J6": date(2026, 6, 30),
    "TTJ26": date(2026, 6, 30),
    "S31L6": date(2026, 7, 31),
    "S31G6": date(2026, 8, 31),
    "TTS26": date(2026, 9, 15),
    "S30O6": date(2026, 10, 30),
    "S30N6": date(2026, 11, 30),
    "TTD26": date(2026, 12, 15),
    "T15E7": date(2027, 1, 15),
    "T30A7": date(2027, 4, 30),
    "T31Y7": date(2027, 5, 31),
    "T30J7": date(2027, 6, 30),
}

# Bond payoff values
PAYOFF = {
    "T17O5": 158.872,
    "S31O5": 132.821,
    "S10N5": 122.254,
    "S28N5": 123.561,
    "T15D5": 170.838,
    "S16E6": 119.06,
    "T30E6": 142.222,
    "T13F6": 144.966,
    "S27F6": 125.84,
    "S16M6": 104.62,
    "TTM26": 152.03,
    "S17A6": 110.13,
    "S30A6": 127.49,
    "S29Y6": 132.04,
    "T30J6": 144.896,
    "TTJ26": 151.49,
    "S31L6": 117.68,
    "S31G6": 127.06,
    "TTS26": 152.10,
    "S30O6": 135.28,
    "S30N6": 129.89,
    "TTD26": 162.21,
    "T15E7": 160.777,
    "T30A7": 157.34,
    "T31Y7": 151.56,
    "T30J7": 156.04,
}

# API endpoints
DATA912_BASE_URL = "https://data912.com/live"
MEP_ENDPOINT = f"{DATA912_BASE_URL}/mep"
NOTES_ENDPOINT = f"{DATA912_BASE_URL}/arg_notes"
BONDS_ENDPOINT = f"{DATA912_BASE_URL}/arg_bonds"

# REM BCRA API - Proyecciones de inflación
REM_API_BASE_URL = "https://bcra-rem-api.facujallia.workers.dev"
REM_IPC_ENDPOINT = f"{REM_API_BASE_URL}/api/ipc_general"

# Currency band parameters - FASE 1 (hasta 31/12/2025)
BAND_PHASE1_BASE_VALUE = 1400  # Base 14 abril 2025
BAND_PHASE1_MONTHLY_RATE = 0.01  # 1% mensual fijo
BAND_PHASE1_START_DATE = date(2025, 4, 14)
BAND_PHASE1_END_DATE = date(2025, 12, 31)

# Currency band parameters - FASE 2 (desde 01/01/2026)
# Bandas evolucionan según inflación T-2 (dos meses atrás)
BAND_PHASE2_START_DATE = date(2026, 1, 1)
BAND_PHASE2_BASE_VALUE = 1526.60  # Banda Superior oficial al 31/12/2025
BAND_PHASE2_LOWER_BASE = 916.28  # Banda Inferior oficial al 31/12/2025

# Últimos datos de inflación conocidos (datos reales publicados por INDEC)
# Estos son datos históricos que ya ocurrieron y no están en las proyecciones del REM
KNOWN_INFLATION_DATA = {
    date(2025, 11, 1): 0.025,  # Noviembre 2025: 2.5% (INDEC)
    date(2025, 12, 1): 0.028,  # Diciembre 2025: 2.8% (INDEC)
    date(2026, 1, 1): 0.029,   # Enero 2026: 2.9% (INDEC)
}

# Mantener retrocompatibilidad
LAST_KNOWN_INFLATION = {
    'month': date(2026, 1, 1),
    'rate': 0.029
}

# Carry trade scenarios
CARRY_SCENARIOS = [1300, 1400, 1500, 1600, 1700, 1800]
