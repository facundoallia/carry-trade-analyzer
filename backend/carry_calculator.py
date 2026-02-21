import pandas as pd
from datetime import date
from typing import Dict, List, Any
from backend.config import (
    TICKERS, PAYOFF, CARRY_SCENARIOS,
    BAND_PHASE1_BASE_VALUE, BAND_PHASE1_MONTHLY_RATE, BAND_PHASE1_START_DATE, BAND_PHASE1_END_DATE,
    BAND_PHASE2_START_DATE, BAND_PHASE2_BASE_VALUE, LAST_KNOWN_INFLATION, KNOWN_INFLATION_DATA
)
from backend.data_fetcher import DataFetcher
from backend.rem_fetcher import REMDataFetcher

class CarryTradeCalculator:
    """Calculate carry trade metrics for Argentine bonds with dynamic inflation-based bands"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.rem_fetcher = REMDataFetcher()
        self._inflation_path_cache = {}  # Caché para evitar recalcular
    
    def _build_calibrated_inflation_path(self, expiration_date: date) -> Dict[str, float]:
        """
        Construye proyección de inflación calibrada usando datos mensuales REM con T-2

        PRIORIDADES:
        1. KNOWN_INFLATION_DATA (datos reales INDEC)
        2. Datos mensuales REM (si disponibles)
        3. Calibración con proyección anual REM
        4. Fallback conservador

        Returns:
            Dict con clave 'YYYY-MM' y valor tasa mensual decimal
        """
        # Usar caché si ya calculamos para este vencimiento
        cache_key = expiration_date.strftime('%Y-%m-%d')
        if cache_key in self._inflation_path_cache:
            return self._inflation_path_cache[cache_key]

        print(f"\n=== Construyendo proyección calibrada hasta {expiration_date.strftime('%Y-%m-%d')} ===")

        # Obtener datos REM (opcional - puede fallar)
        rem_data = self.rem_fetcher.fetch_ipc_projections()
        if not rem_data:
            print("[WARN] No se pudieron obtener datos REM - usando solo datos conocidos + fallback")

        # PASO 1: Construir datos mensuales REM (si disponibles)
        monthly_rem_data = {}
        if rem_data and 'datos' in rem_data:
            for row in rem_data.get('datos', []):
                periodo = row.get('período', '')
                mediana = row.get('mediana', row.get('Mediana'))
                if mediana and periodo:
                    parsed_date = self.rem_fetcher._parse_period_to_date(periodo)
                    if parsed_date:
                        monthly_rem_data[parsed_date] = float(mediana) / 100
                        print(f"  REM data: {periodo} ({parsed_date.strftime('%Y-%m')}) = {float(mediana):.2f}%")

        # PASO 2: Construir inflation_path mes a mes con prioridades
        inflation_path = {}
        max_year = expiration_date.year

        for year in range(BAND_PHASE2_START_DATE.year, max_year + 1):
            for month in range(1, 13):
                month_date = date(year, month, 1)
                month_key = month_date.strftime('%Y-%m')

                # Calcular T-2 (dos meses atrás)
                if month <= 2:
                    t2_month = date(year - 1, month + 10, 1)
                else:
                    t2_month = date(year, month - 2, 1)

                # PRIORIDAD 1: Datos conocidos (INDEC oficial)
                if t2_month in KNOWN_INFLATION_DATA:
                    inflation_path[month_key] = KNOWN_INFLATION_DATA[t2_month]
                    print(f"  {month_key}: {KNOWN_INFLATION_DATA[t2_month]*100:.2f}% (KNOWN, T-2={t2_month.strftime('%Y-%m')})")

                # PRIORIDAD 2: Datos mensuales REM
                elif t2_month in monthly_rem_data:
                    inflation_path[month_key] = monthly_rem_data[t2_month]
                    print(f"  {month_key}: {monthly_rem_data[t2_month]*100:.2f}% (REM, T-2={t2_month.strftime('%Y-%m')})")

                # PRIORIDAD 3: Calibrar después
                else:
                    inflation_path[month_key] = None
                    print(f"  {month_key}: None (T-2={t2_month.strftime('%Y-%m')} pendiente de calibración)")

        # PASO 3: Calibrar meses pendientes por año
        years = {}
        for month_key, rate in inflation_path.items():
            year = int(month_key.split('-')[0])
            if year not in years:
                years[year] = []
            years[year].append((month_key, rate))

        for year, months in sorted(years.items()):
            # Intentar obtener proyección anual del REM
            annual_target = None
            if rem_data:
                annual_target = self.rem_fetcher._get_annual_projection(date(year, 6, 1), rem_data)

            known_months = [(k, v) for k, v in months if v is not None]
            pending_months = [k for k, v in months if v is None]

            if pending_months:
                if annual_target:
                    # Calibrar usando proyección anual
                    known_accumulated = 1.0
                    for _, rate in known_months:
                        known_accumulated *= (1 + rate)

                    target_accumulated = 1 + annual_target
                    remaining_factor = target_accumulated / known_accumulated

                    n_pending = len(pending_months)
                    calibrated_monthly_rate = (remaining_factor ** (1 / n_pending)) - 1

                    print(f"\n  Año {year}: Calibrando {n_pending} meses para {annual_target*100:.2f}% anual")
                    print(f"    Acumulado conocido: {(known_accumulated-1)*100:.2f}%")
                    print(f"    Tasa calibrada: {calibrated_monthly_rate*100:.4f}%")

                    for month_key in pending_months:
                        inflation_path[month_key] = calibrated_monthly_rate
                else:
                    # Sin REM: usar fallback conservador
                    fallback_rate = 0.02  # 2.0% mensual conservador
                    print(f"\n  Año {year}: Sin datos REM - usando fallback {fallback_rate*100:.1f}% para {len(pending_months)} meses")

                    for month_key in pending_months:
                        inflation_path[month_key] = fallback_rate

        # Verificar que NO haya valores None (todos los meses deben tener tasa)
        for month_key, rate in inflation_path.items():
            if rate is None:
                print(f"  [ERROR] {month_key} aún tiene valor None - aplicando fallback 2.0%")
                inflation_path[month_key] = 0.02

        self._inflation_path_cache[cache_key] = inflation_path
        return inflation_path
    
    def calculate_band_ceiling(self, expiration_date: date) -> float:
        """
        Calculate currency band ceiling with two-phase model:
        - Phase 1 (hasta 31/12/2025): 1% mensual aplicado diariamente
        - Phase 2 (desde 01/01/2026): Inflación T-2 calibrada aplicada diariamente
        
        La tasa mensual se distribuye día a día de forma compuesta.
        Por ejemplo: 2.5% en enero = (1.025)^(1/31) - 1 por día
        Al final del mes acumula exactamente 2.5%
        """
        from datetime import timedelta
        from calendar import monthrange
        
        # FASE 1: Hasta 31/12/2025 - Crawling peg fijo 1% mensual aplicado diariamente
        if expiration_date <= BAND_PHASE1_END_DATE:
            days_since_start = (expiration_date - BAND_PHASE1_START_DATE).days
            return BAND_PHASE1_BASE_VALUE * (1 + BAND_PHASE1_MONTHLY_RATE) ** (days_since_start / 30)
        
        # Para bonos que vencen después de 31/12/2025:
        # 1. Calcular banda al 31/12/2025 (valor base conocido)
        current_ceiling = BAND_PHASE2_BASE_VALUE  # $1,526.60 al 31/12/2025
        
        # 2. Si hoy es antes del 31/12/2025, calcular banda de hoy usando Fase 1
        today = date.today()
        if today < BAND_PHASE2_START_DATE:
            # Estamos en Fase 1 hoy, calcular banda actual
            days_since_start = (today - BAND_PHASE1_START_DATE).days
            current_ceiling = BAND_PHASE1_BASE_VALUE * (1 + BAND_PHASE1_MONTHLY_RATE) ** (days_since_start / 30)
            
            # Proyectar desde hoy hasta 31/12/2025 con Fase 1
            current_date = today
            days_in_december = monthrange(2025, 12)[1]
            daily_rate_phase1 = (1 + BAND_PHASE1_MONTHLY_RATE) ** (1 / days_in_december) - 1
            
            while current_date < BAND_PHASE2_START_DATE:
                current_ceiling = current_ceiling * (1 + daily_rate_phase1)
                current_date = current_date + timedelta(days=1)
        
        # 3. FASE 2: Proyectar desde 01/01/2026 hasta vencimiento con inflación calibrada
        inflation_path = self._build_calibrated_inflation_path(expiration_date)
        
        current_date = BAND_PHASE2_START_DATE
        current_month_key = None
        daily_rate = None
        
        while current_date <= expiration_date:
            month_key = current_date.strftime('%Y-%m')
            
            # Al inicio de cada mes, calcular la tasa diaria
            if month_key != current_month_key:
                current_month_key = month_key
                monthly_rate = inflation_path.get(month_key, 0.015)  # Fallback 1.5%
                
                days_in_month = monthrange(current_date.year, current_date.month)[1]
                daily_rate = (1 + monthly_rate) ** (1 / days_in_month) - 1
            
            # Aplicar tasa diaria
            current_ceiling = current_ceiling * (1 + daily_rate)
            current_date = current_date + timedelta(days=1)
        
        return current_ceiling
    
    def calculate_carry_metrics(self) -> pd.DataFrame:
        """Calculate all carry trade metrics matching the original notebook logic"""
        
        # Fetch market data
        market_data = self.data_fetcher.fetch_all_data()
        mep_rate = market_data['mep_rate']
        
        if not market_data['instruments'] or mep_rate is None:
            return pd.DataFrame()
        
        # Create DataFrame from instruments
        df = pd.DataFrame(market_data['instruments'])
        carry = df.loc[df.symbol.isin(TICKERS.keys())].set_index('symbol')
        
        # Basic bond information
        carry['bond_price'] = carry['c'].round(2)
        carry['payoff'] = carry.index.map(PAYOFF)
        carry['expiration'] = carry.index.map(TICKERS)
        carry['days_to_exp'] = (carry.expiration - date.today()).apply(lambda x: x.days)

        # Filter out expired bonds
        carry = carry[carry['days_to_exp'] > 0]

        if carry.empty:
            return pd.DataFrame()

        # Calculate rates
        carry['tna'] = ((carry['payoff'] / carry['c']) - 1) / carry['days_to_exp'] * 365
        carry['tea'] = ((carry['payoff'] / carry['c'])) ** (365/carry['days_to_exp']) - 1
        carry['tem'] = ((carry['payoff'] / carry['c'])) ** (1/(carry['days_to_exp']/30)) - 1
        
        # Calculate band ceiling using expiration date
        carry['finish_worst'] = carry['expiration'].apply(self.calculate_band_ceiling).round().astype(int)
        
        # Calculate carry trade scenarios - solo para precios <= banda al vencimiento
        for price in CARRY_SCENARIOS:
            # Si el precio del escenario es mayor a la banda, el carry es NaN (escenario inválido)
            carry[f'carry_{price}'] = carry.apply(
                lambda row: (row['payoff'] / row['c']) * mep_rate / price - 1 
                if price <= row['finish_worst'] 
                else float('nan'), 
                axis=1
            )
        
        # Calculate carry at band ceiling
        carry['carry_worst'] = (carry['payoff'] / carry['c']) * mep_rate / carry['finish_worst'] - 1
        
        # Calculate MEP breakeven
        carry['mep_breakeven'] = mep_rate * (carry['payoff'] / carry['c'])
        
        # Sort by days to expiration
        carry = carry.sort_values('days_to_exp')
        
        return carry
    
    def get_table_data(self) -> List[Dict[str, Any]]:
        """Get formatted data for the web table"""
        carry_df = self.calculate_carry_metrics()
        
        if carry_df.empty:
            return []
        
        table_data = []
        for ticker in carry_df.index:
            row = {'ticker': str(ticker)}
            row['precio'] = float(carry_df.loc[ticker, 'bond_price'])
            row['fecha_vencimiento'] = carry_df.loc[ticker, 'expiration'].strftime('%d/%m/%Y')
            row['dias_vencimiento'] = int(carry_df.loc[ticker, 'days_to_exp'])
            row['tem'] = float(carry_df.loc[ticker, 'tem'])
            row['tna'] = float(carry_df.loc[ticker, 'tna'])
            row['tea'] = float(carry_df.loc[ticker, 'tea'])
            
            # Carry scenarios - convert numpy types to native Python types, NaN to special string
            import math
            for price in CARRY_SCENARIOS:
                carry_val = float(carry_df.loc[ticker, f'carry_{price}'])
                row[f'carry_{price}'] = "-" if math.isnan(carry_val) else carry_val
            
            row['carry_techo'] = float(carry_df.loc[ticker, 'carry_worst'])
            
            table_data.append(row)
        
        return table_data
    
    def get_chart_data(self) -> Dict[str, Any]:
        """Get data for the breakeven vs band ceiling chart with temporal scale"""
        carry_df = self.calculate_carry_metrics()

        if carry_df.empty:
            return {}

        # Generate band projection with weekly points for smooth curve
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        first_exp = carry_df['expiration'].min()
        last_exp = carry_df['expiration'].max()

        # Start at today, extend 1 month beyond last expiration
        current_date = date.today()
        end_date = last_exp + relativedelta(months=1)

        band_projection_dates = []
        band_projection_values = []

        # Generate points every 7 days for smooth curve
        while current_date <= end_date:
            band_value = self.calculate_band_ceiling(current_date)
            band_projection_dates.append(current_date.strftime('%Y-%m-%d'))
            band_projection_values.append(float(band_value))

            # Move forward 7 days
            current_date = current_date + timedelta(days=7)

        chart_data = {
            'tickers': [str(ticker) for ticker in carry_df.index.tolist()],
            'band_ceiling': [float(val) for val in carry_df['finish_worst'].tolist()],
            'mep_breakeven': [float(val) for val in carry_df['mep_breakeven'].tolist()],
            'days_to_exp': [int(val) for val in carry_df['days_to_exp'].tolist()],
            'expiration_dates': [exp_date.strftime('%Y-%m-%d') for exp_date in carry_df['expiration'].tolist()],
            # New: Monthly band projection
            'band_projection_dates': band_projection_dates,
            'band_projection_values': band_projection_values
        }

        return chart_data
    
    def get_color_limits(self) -> Dict[str, float]:
        """Get color gradient limits for the table"""
        carry_df = self.calculate_carry_metrics()
        
        if carry_df.empty:
            return {'vmin': 0.0, 'vmax': 0.0, 'limit': 0.0}
        
        # Calculate limits for carry columns
        carry_columns = [f'carry_{price}' for price in CARRY_SCENARIOS] + ['carry_worst']
        carry_values = carry_df[carry_columns]
        
        vmax = float(carry_values.max().max())
        vmin = float(carry_values.min().min())
        limit = float(max(abs(vmin), abs(vmax)) * 0.3)
        
        return {
            'vmin': -limit,
            'vmax': limit,
            'limit': limit
        }
    
    def get_mep_rate(self) -> float:
        """Get current MEP rate"""
        market_data = self.data_fetcher.fetch_all_data()
        return market_data.get('mep_rate')