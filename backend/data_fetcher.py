import requests
import pandas as pd
import os
from datetime import date
from typing import Dict, Any, List
from backend.config import MEP_ENDPOINT, NOTES_ENDPOINT, BONDS_ENDPOINT, TICKERS

class DataFetcher:
    """Fetches real-time financial data from data912.com API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Production timeout configuration
        self.timeout = int(os.getenv("API_TIMEOUT", 10))
        
    def _make_request(self, url: str, timeout: int = None) -> requests.Response:
        """Make HTTP request with proper timeout and error handling"""
        timeout = timeout or self.timeout
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"Timeout error for {url}")
            raise
        except requests.exceptions.ConnectionError:
            print(f"Connection error for {url}")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error for {url}: {e}")
            raise
    
    def fetch_mep_data(self) -> float:
        """Fetch MEP (Dollar Blue) exchange rate"""
        try:
            response = self._make_request(MEP_ENDPOINT)
            mep_data = response.json()
            
            # Debug: Print structure of MEP data
            print(f"MEP data structure: {type(mep_data)}")
            if isinstance(mep_data, list) and len(mep_data) > 0:
                print(f"First MEP item: {mep_data[0]}")
            elif isinstance(mep_data, dict):
                print(f"MEP data keys: {list(mep_data.keys())}")
            
            # Handle different possible data structures
            if isinstance(mep_data, list):
                df = pd.DataFrame(mep_data)
                if 'close' in df.columns:
                    return df['close'].median()
                elif 'value' in df.columns:
                    return df['value'].median()
                elif 'price' in df.columns:
                    return df['price'].median()
                else:
                    # Try to find numeric columns
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        return df[numeric_cols[0]].median()
                    else:
                        print(f"No numeric columns found in MEP data: {df.columns.tolist()}")
                        return 1200.0  # Fallback value
            elif isinstance(mep_data, dict):
                # Try different possible keys
                for key in ['close', 'value', 'price', 'last', 'rate']:
                    if key in mep_data:
                        return float(mep_data[key])
                
                # If no standard key found, try to find numeric value
                for key, value in mep_data.items():
                    if isinstance(value, (int, float)):
                        return float(value)
                        
                print(f"No numeric value found in MEP data: {mep_data}")
                return 1200.0  # Fallback value
            else:
                print(f"Unexpected MEP data format: {type(mep_data)}")
                return float(os.getenv("DEFAULT_MEP_RATE", 1200.0))  # Fallback value
                
        except Exception as e:
            print(f"Error fetching MEP data: {e}")
            return float(os.getenv("DEFAULT_MEP_RATE", 1200.0))  # Fallback value
    
    def fetch_bonds_data(self) -> List[Dict[str, Any]]:
        """Fetch Argentine bonds data"""
        try:
            response = self._make_request(BONDS_ENDPOINT)
            bonds_data = response.json()
            
            # Validate data structure
            if not isinstance(bonds_data, list):
                print(f"Warning: Expected list for bonds data, got {type(bonds_data)}")
                return []
            
            return bonds_data
        except Exception as e:
            print(f"Error fetching bonds data: {e}")
            return []
    
    def fetch_notes_data(self) -> List[Dict[str, Any]]:
        """Fetch Argentine notes data"""
        try:
            response = self._make_request(NOTES_ENDPOINT)
            notes_data = response.json()
            
            # Validate data structure
            if not isinstance(notes_data, list):
                print(f"Warning: Expected list for notes data, got {type(notes_data)}")
                return []
            
            return notes_data
        except Exception as e:
            print(f"Error fetching notes data: {e}")
            return []
    
    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all required data in one call"""
        mep_rate = self.fetch_mep_data()
        bonds_data = self.fetch_bonds_data()
        notes_data = self.fetch_notes_data()
        
        # Validate MEP rate
        if mep_rate is None or mep_rate <= 0:
            fallback_rate = float(os.getenv("DEFAULT_MEP_RATE", 1200.0))
            print(f"Warning: Invalid MEP rate {mep_rate}, using fallback value {fallback_rate}")
            mep_rate = fallback_rate
        
        # Combine bonds and notes data
        all_instruments = bonds_data + notes_data
        
        # Filter for relevant tickers
        relevant_data = []
        for instrument in all_instruments:
            if isinstance(instrument, dict) and instrument.get('symbol') in TICKERS:
                relevant_data.append(instrument)
        
        print(f"Fetched {len(relevant_data)} relevant instruments out of {len(all_instruments)} total")
        print(f"MEP rate: {mep_rate}")
        
        return {
            'mep_rate': mep_rate,
            'instruments': relevant_data,
            'fetch_date': date.today().isoformat(),
            'data_status': {
                'mep_success': mep_rate > 0,
                'bonds_count': len(bonds_data),
                'notes_count': len(notes_data),
                'relevant_count': len(relevant_data)
            }
        }
    
    def get_instrument_dataframe(self) -> pd.DataFrame:
        """Get instruments data as a pandas DataFrame"""
        data = self.fetch_all_data()
        if not data['instruments']:
            return pd.DataFrame()
        
        df = pd.DataFrame(data['instruments'])
        df = df.set_index('symbol')
        return df