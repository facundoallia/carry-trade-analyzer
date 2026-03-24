"""
CarryTradeCalculator — lógica central del carry trade
Adaptado para Vercel serverless: imports locales (sin prefijo backend.)
"""
import pandas as pd
import math
from datetime import date, timedelta
from calendar import monthrange
from typing import Dict, List, Any, Optional
from dateutil.relativedelta import relativedelta

from config import (
    TICKERS, PAYOFF, CARRY_SCENARIOS,
    BAND_PHASE1_BASE_VALUE, BAND_PHASE1_MONTHLY_RATE,
    BAND_PHASE1_START_DATE, BAND_PHASE1_END_DATE,
    BAND_PHASE2_START_DATE, BAND_PHASE2_BASE_VALUE,
    LAST_KNOWN_INFLATION, KNOWN_INFLATION_DATA
)
from data_fetcher import DataFetcher
from rem_fetcher import REMDataFetcher


class CarryTradeCalculator:
    """Calcula métricas de carry trade para bonos argentinos con bandas dinámicas"""

    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.rem_fetcher = REMDataFetcher()
        self._inflation_path_cache = {}

    def _build_calibrated_inflation_path(self, expiration_date: date) -> Dict[str, float]:
        cache_key = expiration_date.strftime('%Y-%m-%d')
        if cache_key in self._inflation_path_cache:
            return self._inflation_path_cache[cache_key]

        rem_data = self.rem_fetcher.fetch_ipc_projections()
        if not rem_data:
            print("[WARN] No se pudieron obtener datos REM — usando datos conocidos + fallback")

        monthly_rem_data = {}
        if rem_data and 'datos' in rem_data:
            for row in rem_data.get('datos', []):
                periodo = row.get('período', '')
                mediana = row.get('mediana', row.get('Mediana'))
                if mediana and periodo:
                    parsed_date = self.rem_fetcher._parse_period_to_date(periodo)
                    if parsed_date:
                        monthly_rem_data[parsed_date] = float(mediana) / 100

        inflation_path = {}
        max_year = expiration_date.year

        for year in range(BAND_PHASE2_START_DATE.year, max_year + 1):
            for month in range(1, 13):
                month_date = date(year, month, 1)
                month_key = month_date.strftime('%Y-%m')
                t2_month = date(year - 1, month + 10, 1) if month <= 2 else date(year, month - 2, 1)

                if t2_month in KNOWN_INFLATION_DATA:
                    inflation_path[month_key] = KNOWN_INFLATION_DATA[t2_month]
                elif t2_month in monthly_rem_data:
                    inflation_path[month_key] = monthly_rem_data[t2_month]
                else:
                    inflation_path[month_key] = None

        # Calibrar meses pendientes por año
        years = {}
        for month_key, rate in inflation_path.items():
            year = int(month_key.split('-')[0])
            years.setdefault(year, []).append((month_key, rate))

        for year, months in sorted(years.items()):
            annual_target = None
            if rem_data:
                annual_target = self.rem_fetcher._get_annual_projection(date(year, 6, 1), rem_data)

            known_months = [(k, v) for k, v in months if v is not None]
            pending_months = [k for k, v in months if v is None]

            if pending_months:
                if annual_target:
                    known_accumulated = 1.0
                    for _, rate in known_months:
                        known_accumulated *= (1 + rate)
                    target_accumulated = 1 + annual_target
                    remaining_factor = target_accumulated / known_accumulated
                    n_pending = len(pending_months)
                    calibrated_rate = (remaining_factor ** (1 / n_pending)) - 1
                    for month_key in pending_months:
                        inflation_path[month_key] = calibrated_rate
                else:
                    for month_key in pending_months:
                        inflation_path[month_key] = 0.02  # 2% fallback

        # Asegurar que no hay Nones
        for month_key in inflation_path:
            if inflation_path[month_key] is None:
                inflation_path[month_key] = 0.02

        self._inflation_path_cache[cache_key] = inflation_path
        return inflation_path

    def calculate_band_ceiling(self, expiration_date: date) -> float:
        """
        Calcula el techo de la banda cambiaria con modelo de dos fases:
        - Fase 1 (hasta 31/12/2025): 1% mensual aplicado diariamente
        - Fase 2 (desde 01/01/2026): inflación T-2 calibrada aplicada diariamente
        """
        if expiration_date <= BAND_PHASE1_END_DATE:
            days_since_start = (expiration_date - BAND_PHASE1_START_DATE).days
            return BAND_PHASE1_BASE_VALUE * (1 + BAND_PHASE1_MONTHLY_RATE) ** (days_since_start / 30)

        current_ceiling = BAND_PHASE2_BASE_VALUE
        today = date.today()

        if today < BAND_PHASE2_START_DATE:
            days_since_start = (today - BAND_PHASE1_START_DATE).days
            current_ceiling = BAND_PHASE1_BASE_VALUE * (1 + BAND_PHASE1_MONTHLY_RATE) ** (days_since_start / 30)
            current_date = today
            days_in_december = monthrange(2025, 12)[1]
            daily_rate_phase1 = (1 + BAND_PHASE1_MONTHLY_RATE) ** (1 / days_in_december) - 1
            while current_date < BAND_PHASE2_START_DATE:
                current_ceiling *= (1 + daily_rate_phase1)
                current_date += timedelta(days=1)

        inflation_path = self._build_calibrated_inflation_path(expiration_date)
        current_date = BAND_PHASE2_START_DATE
        current_month_key = None
        daily_rate = None

        while current_date <= expiration_date:
            month_key = current_date.strftime('%Y-%m')
            if month_key != current_month_key:
                current_month_key = month_key
                monthly_rate = inflation_path.get(month_key, 0.015)
                days_in_month = monthrange(current_date.year, current_date.month)[1]
                daily_rate = (1 + monthly_rate) ** (1 / days_in_month) - 1
            current_ceiling *= (1 + daily_rate)
            current_date += timedelta(days=1)

        return current_ceiling

    def calculate_carry_metrics(self) -> pd.DataFrame:
        """Calcula todas las métricas de carry trade"""
        market_data = self.data_fetcher.fetch_all_data()
        mep_rate = market_data['mep_rate']

        if not market_data['instruments'] or mep_rate is None:
            return pd.DataFrame()

        df = pd.DataFrame(market_data['instruments'])
        carry = df.loc[df.symbol.isin(TICKERS.keys())].set_index('symbol')

        carry['bond_price'] = carry['c'].round(2)
        carry['payoff'] = carry.index.map(PAYOFF)
        carry['expiration'] = carry.index.map(TICKERS)
        carry['days_to_exp'] = (carry.expiration - date.today()).apply(lambda x: x.days)
        carry = carry[carry['days_to_exp'] > 0]

        if carry.empty:
            return pd.DataFrame()

        carry['tna'] = ((carry['payoff'] / carry['c']) - 1) / carry['days_to_exp'] * 365
        carry['tea'] = ((carry['payoff'] / carry['c'])) ** (365 / carry['days_to_exp']) - 1
        carry['tem'] = ((carry['payoff'] / carry['c'])) ** (1 / (carry['days_to_exp'] / 30)) - 1
        carry['finish_worst'] = carry['expiration'].apply(self.calculate_band_ceiling).round().astype(int)

        for price in CARRY_SCENARIOS:
            carry[f'carry_{price}'] = carry.apply(
                lambda row: (row['payoff'] / row['c']) * mep_rate / price - 1
                if price <= row['finish_worst']
                else float('nan'),
                axis=1
            )

        carry['carry_worst'] = (carry['payoff'] / carry['c']) * mep_rate / carry['finish_worst'] - 1
        carry['mep_breakeven'] = mep_rate * (carry['payoff'] / carry['c'])
        carry = carry.sort_values('days_to_exp')

        return carry

    def get_table_data(self) -> List[Dict[str, Any]]:
        carry_df = self.calculate_carry_metrics()
        if carry_df.empty:
            return []

        table_data = []
        for ticker in carry_df.index:
            row = {
                'ticker': str(ticker),
                'precio': float(carry_df.loc[ticker, 'bond_price']),
                'fecha_vencimiento': carry_df.loc[ticker, 'expiration'].strftime('%d/%m/%Y'),
                'dias_vencimiento': int(carry_df.loc[ticker, 'days_to_exp']),
                'tem': float(carry_df.loc[ticker, 'tem']),
                'tna': float(carry_df.loc[ticker, 'tna']),
                'tea': float(carry_df.loc[ticker, 'tea']),
            }
            for price in CARRY_SCENARIOS:
                val = float(carry_df.loc[ticker, f'carry_{price}'])
                row[f'carry_{price}'] = '-' if math.isnan(val) else val
            row['carry_techo'] = float(carry_df.loc[ticker, 'carry_worst'])
            table_data.append(row)

        return table_data

    def get_chart_data(self) -> Dict[str, Any]:
        carry_df = self.calculate_carry_metrics()
        if carry_df.empty:
            return {}

        first_exp = carry_df['expiration'].min()
        last_exp = carry_df['expiration'].max()
        current_date = date.today()
        end_date = last_exp + relativedelta(months=1)

        band_projection_dates = []
        band_projection_values = []

        while current_date <= end_date:
            band_value = self.calculate_band_ceiling(current_date)
            band_projection_dates.append(current_date.strftime('%Y-%m-%d'))
            band_projection_values.append(float(band_value))
            current_date += timedelta(days=7)

        return {
            'tickers': [str(t) for t in carry_df.index.tolist()],
            'band_ceiling': [float(v) for v in carry_df['finish_worst'].tolist()],
            'mep_breakeven': [float(v) for v in carry_df['mep_breakeven'].tolist()],
            'days_to_exp': [int(v) for v in carry_df['days_to_exp'].tolist()],
            'expiration_dates': [d.strftime('%Y-%m-%d') for d in carry_df['expiration'].tolist()],
            'band_projection_dates': band_projection_dates,
            'band_projection_values': band_projection_values,
        }

    def get_color_limits(self) -> Dict[str, float]:
        carry_df = self.calculate_carry_metrics()
        if carry_df.empty:
            return {'vmin': 0.0, 'vmax': 0.0, 'limit': 0.0}

        carry_columns = [f'carry_{price}' for price in CARRY_SCENARIOS] + ['carry_worst']
        carry_values = carry_df[carry_columns]
        vmax = float(carry_values.max().max())
        vmin = float(carry_values.min().min())
        limit = float(max(abs(vmin), abs(vmax)) * 0.3)
        return {'vmin': -limit, 'vmax': limit, 'limit': limit}

    def get_mep_rate(self) -> Optional[float]:
        market_data = self.data_fetcher.fetch_all_data()
        return market_data.get('mep_rate')
