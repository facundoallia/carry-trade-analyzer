import requests
import pandas as pd
import os
import json
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.config import MEP_ENDPOINT, NOTES_ENDPOINT, BONDS_ENDPOINT, TICKERS
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Persistent MEP storage file
LAST_MEP_FILE = Path(__file__).parent.parent / "cache" / "last_mep.json"

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

    def _save_last_known_mep(self, rate: float):
        """Save last known good MEP rate to persistent file"""
        try:
            LAST_MEP_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"rate": rate, "date": datetime.now().isoformat()}
            LAST_MEP_FILE.write_text(json.dumps(data))
        except Exception as e:
            print(f"Warning: Could not save last known MEP: {e}")

    def _load_last_known_mep(self) -> Optional[float]:
        """Load last known good MEP rate from persistent file"""
        try:
            if LAST_MEP_FILE.exists():
                data = json.loads(LAST_MEP_FILE.read_text())
                rate = data.get("rate", 0)
                if rate > 500:
                    print(f"Using last known MEP rate: {rate} from {data.get('date', 'unknown')}")
                    return rate
        except Exception as e:
            print(f"Warning: Could not load last known MEP: {e}")
        return None

    def _calculate_mep_from_bonds(self) -> Optional[float]:
        """Calculate MEP rate from bond ARS/USD price pairs as fallback"""
        try:
            response = self._make_request(BONDS_ENDPOINT, timeout=15)
            bonds = response.json()

            if not isinstance(bonds, list) or not bonds:
                return None

            # Index by symbol
            by_symbol = {}
            for bond in bonds:
                sym = bond.get('symbol', '')
                price = float(bond.get('c', 0) or 0)
                if sym and price > 0:
                    by_symbol[sym] = price

            # Calculate MEP from liquid bond pairs (ARS / USD-D)
            mep_pairs = ['GD30', 'AL30', 'GD29', 'AL29', 'GD35', 'AL35', 'AE38', 'GD38']
            mep_values = []
            for base in mep_pairs:
                ars_sym = base
                usd_sym = f"{base}D"
                if ars_sym in by_symbol and usd_sym in by_symbol and by_symbol[usd_sym] > 0:
                    mep = by_symbol[ars_sym] / by_symbol[usd_sym]
                    if 500 < mep < 5000:  # Sanity check
                        mep_values.append(mep)
                        print(f"MEP from {base}: {mep:.2f}")

            if not mep_values:
                return None

            # Return median
            mep_values.sort()
            n = len(mep_values)
            if n % 2 == 0:
                median = (mep_values[n // 2 - 1] + mep_values[n // 2]) / 2
            else:
                median = mep_values[n // 2]

            print(f"MEP calculated from {len(mep_values)} bond pairs: {median:.2f}")
            return round(median, 2)
        except Exception as e:
            print(f"Error calculating MEP from bonds: {e}")
            return None

    def fetch_mep_data(self) -> Optional[float]:
        """Fetch MEP (Dollar MEP) exchange rate with multiple fallbacks"""
        mep_rate = None

        # Try 1: Dedicated MEP endpoint
        try:
            response = self._make_request(MEP_ENDPOINT)
            mep_data = response.json()

            if isinstance(mep_data, list):
                df = pd.DataFrame(mep_data)
                for col in ['close', 'value', 'price']:
                    if col in df.columns:
                        mep_rate = float(df[col].median())
                        break
                if mep_rate is None:
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        mep_rate = float(df[numeric_cols[0]].median())
            elif isinstance(mep_data, dict):
                for key in ['close', 'value', 'price', 'last', 'rate']:
                    if key in mep_data:
                        mep_rate = float(mep_data[key])
                        break
                if mep_rate is None:
                    for key, value in mep_data.items():
                        if isinstance(value, (int, float)):
                            mep_rate = float(value)
                            break
        except Exception as e:
            print(f"MEP endpoint failed: {e}")

        # Validate MEP from endpoint
        if mep_rate is not None and 500 < mep_rate < 5000:
            self._save_last_known_mep(mep_rate)
            return mep_rate

        # Try 2: Calculate from bond pairs
        print("MEP endpoint empty/invalid, calculating from bond pairs")
        mep_rate = self._calculate_mep_from_bonds()
        if mep_rate is not None:
            self._save_last_known_mep(mep_rate)
            return mep_rate

        # Try 3: Last known good MEP from persistent storage
        last_known = self._load_last_known_mep()
        if last_known is not None:
            return last_known

        print("ERROR: All MEP sources failed, no historical data available")
        return None

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
            print(f"Warning: No valid MEP rate available")
            mep_rate = None

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
                'mep_success': mep_rate is not None and mep_rate > 0,
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
