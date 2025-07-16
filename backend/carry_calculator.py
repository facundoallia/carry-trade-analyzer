import pandas as pd
from datetime import date
from typing import Dict, List, Any
from backend.config import TICKERS, PAYOFF, CARRY_SCENARIOS, BAND_BASE_VALUE, BAND_MONTHLY_RATE
from backend.data_fetcher import DataFetcher

class CarryTradeCalculator:
    """Calculate carry trade metrics for Argentine bonds"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    def calculate_band_ceiling(self, expiration_date: date) -> float:
        """Calculate currency band ceiling based on fixed crawling peg starting from April 14, 2025"""
        band_start_date = date(2025, 4, 14)
        days_since_start = (expiration_date - band_start_date).days
        return BAND_BASE_VALUE * (1 + BAND_MONTHLY_RATE) ** (days_since_start / 30)
    
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
        
        # Calculate rates
        carry['tna'] = ((carry['payoff'] / carry['c']) - 1) / carry['days_to_exp'] * 365
        carry['tea'] = ((carry['payoff'] / carry['c'])) ** (365/carry['days_to_exp']) - 1
        carry['tem'] = ((carry['payoff'] / carry['c'])) ** (1/(carry['days_to_exp']/30)) - 1
        
        # Calculate band ceiling using expiration date
        carry['finish_worst'] = carry['expiration'].apply(self.calculate_band_ceiling).round().astype(int)
        
        # Calculate carry trade scenarios
        for price in CARRY_SCENARIOS:
            carry[f'carry_{price}'] = (carry['payoff'] / carry['c']) * mep_rate / price - 1
        
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
        
        # Select columns for the table
        table_columns = [
            'bond_price', 'days_to_exp', 'tem',
            'carry_1000', 'carry_1100', 'carry_1200', 
            'carry_1300', 'carry_1400', 'carry_worst'
        ]
        
        table_data = []
        for ticker in carry_df.index:
            row = {'ticker': str(ticker)}
            row['precio'] = float(carry_df.loc[ticker, 'bond_price'])
            row['fecha_vencimiento'] = carry_df.loc[ticker, 'expiration'].strftime('%d/%m/%Y')
            row['dias_vencimiento'] = int(carry_df.loc[ticker, 'days_to_exp'])
            row['tem'] = float(carry_df.loc[ticker, 'tem'])
            row['tna'] = float(carry_df.loc[ticker, 'tna'])
            row['tea'] = float(carry_df.loc[ticker, 'tea'])
            
            # Carry scenarios - convert numpy types to native Python types
            row['carry_1000'] = float(carry_df.loc[ticker, 'carry_1000'])
            row['carry_1100'] = float(carry_df.loc[ticker, 'carry_1100'])
            row['carry_1200'] = float(carry_df.loc[ticker, 'carry_1200'])
            row['carry_1300'] = float(carry_df.loc[ticker, 'carry_1300'])
            row['carry_1400'] = float(carry_df.loc[ticker, 'carry_1400'])
            row['carry_techo'] = float(carry_df.loc[ticker, 'carry_worst'])
            
            table_data.append(row)
        
        return table_data
    
    def get_chart_data(self) -> Dict[str, Any]:
        """Get data for the breakeven vs band ceiling chart"""
        carry_df = self.calculate_carry_metrics()
        
        if carry_df.empty:
            return {}
        
        chart_data = {
            'tickers': [str(ticker) for ticker in carry_df.index.tolist()],
            'band_ceiling': [float(val) for val in carry_df['finish_worst'].tolist()],
            'mep_breakeven': [float(val) for val in carry_df['mep_breakeven'].tolist()],
            'days_to_exp': [int(val) for val in carry_df['days_to_exp'].tolist()]
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
        return market_data.get('mep_rate', 1200.0)