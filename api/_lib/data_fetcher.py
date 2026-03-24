"""
DataFetcher — obtiene datos en tiempo real de data912.com
Adaptado para Vercel serverless: sin persistencia en disco, cache en memoria + /tmp
"""
import requests
import pandas as pd
import json
import time
import os
import warnings
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from config import MEP_ENDPOINT, NOTES_ENDPOINT, BONDS_ENDPOINT, TICKERS

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cache de datos a nivel de módulo (persiste entre requests cálidos)
_data_cache: Dict = {'data': None, 'timestamp': 0.0}
_CACHE_TTL = 30  # segundos

# Fallback MEP en memoria (reemplaza last_mep.json en entorno serverless)
_last_known_mep: Optional[float] = None


class DataFetcher:
    """Fetches real-time financial data from data912.com API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = int(os.getenv("API_TIMEOUT", 10))

    def _make_request(self, url: str, timeout: int = None) -> requests.Response:
        timeout = timeout or self.timeout
        try:
            response = self.session.get(url, timeout=timeout, verify=False)
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
        """Guarda MEP en memoria global + /tmp para warm-start fallback"""
        global _last_known_mep
        _last_known_mep = rate
        # Intentar persistir en /tmp (disponible en Vercel serverless)
        try:
            tmp_file = '/tmp/last_mep.json'
            data = {"rate": rate, "date": datetime.now().isoformat()}
            with open(tmp_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_last_known_mep(self) -> Optional[float]:
        """Carga último MEP conocido desde memoria o /tmp"""
        global _last_known_mep
        if _last_known_mep and _last_known_mep > 500:
            print(f"Using in-memory last known MEP: {_last_known_mep}")
            return _last_known_mep
        try:
            tmp_file = '/tmp/last_mep.json'
            if os.path.exists(tmp_file):
                with open(tmp_file, 'r') as f:
                    data = json.load(f)
                rate = data.get("rate", 0)
                if rate > 500:
                    print(f"Using /tmp last known MEP: {rate}")
                    return rate
        except Exception:
            pass
        return None

    def _calculate_mep_from_bonds(self) -> Optional[float]:
        """Calcula MEP desde pares ARS/USD de bonos como fallback"""
        try:
            response = self._make_request(BONDS_ENDPOINT, timeout=15)
            bonds = response.json()
            if not isinstance(bonds, list) or not bonds:
                return None
            by_symbol = {}
            for bond in bonds:
                sym = bond.get('symbol', '')
                price = float(bond.get('c', 0) or 0)
                if sym and price > 0:
                    by_symbol[sym] = price
            mep_pairs = ['GD30', 'AL30', 'GD29', 'AL29', 'GD35', 'AL35', 'AE38', 'GD38']
            mep_values = []
            for base in mep_pairs:
                ars_sym = base
                usd_sym = f"{base}D"
                if ars_sym in by_symbol and usd_sym in by_symbol and by_symbol[usd_sym] > 0:
                    mep = by_symbol[ars_sym] / by_symbol[usd_sym]
                    if 500 < mep < 5000:
                        mep_values.append(mep)
            if not mep_values:
                return None
            mep_values.sort()
            n = len(mep_values)
            median = (mep_values[n // 2 - 1] + mep_values[n // 2]) / 2 if n % 2 == 0 else mep_values[n // 2]
            print(f"MEP calculated from {len(mep_values)} bond pairs: {median:.2f}")
            return round(median, 2)
        except Exception as e:
            print(f"Error calculating MEP from bonds: {e}")
            return None

    def fetch_mep_data(self) -> Optional[float]:
        """Obtiene tasa MEP con múltiples fallbacks"""
        mep_rate = None
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
        except Exception as e:
            print(f"MEP endpoint failed: {e}")

        if mep_rate is not None and 500 < mep_rate < 5000:
            self._save_last_known_mep(mep_rate)
            return mep_rate

        print("MEP endpoint empty/invalid, calculating from bond pairs")
        mep_rate = self._calculate_mep_from_bonds()
        if mep_rate is not None:
            self._save_last_known_mep(mep_rate)
            return mep_rate

        last_known = self._load_last_known_mep()
        if last_known is not None:
            return last_known

        print("ERROR: All MEP sources failed")
        return None

    def fetch_bonds_data(self) -> List[Dict[str, Any]]:
        try:
            response = self._make_request(BONDS_ENDPOINT)
            bonds_data = response.json()
            if not isinstance(bonds_data, list):
                return []
            return bonds_data
        except Exception as e:
            print(f"Error fetching bonds data: {e}")
            return []

    def fetch_notes_data(self) -> List[Dict[str, Any]]:
        try:
            response = self._make_request(NOTES_ENDPOINT)
            notes_data = response.json()
            if not isinstance(notes_data, list):
                return []
            return notes_data
        except Exception as e:
            print(f"Error fetching notes data: {e}")
            return []

    def fetch_all_data(self) -> Dict[str, Any]:
        """
        Obtiene todos los datos necesarios con cache TTL de 30 segundos.
        El cache a nivel de módulo evita llamadas duplicadas en la misma invocación.
        """
        global _data_cache
        now = time.time()

        if _data_cache['data'] is not None and (now - _data_cache['timestamp']) < _CACHE_TTL:
            print(f"Using cached market data ({now - _data_cache['timestamp']:.1f}s old)")
            return _data_cache['data']

        mep_rate = self.fetch_mep_data()
        bonds_data = self.fetch_bonds_data()
        notes_data = self.fetch_notes_data()

        if mep_rate is None or mep_rate <= 0:
            mep_rate = None

        all_instruments = bonds_data + notes_data
        relevant_data = [
            inst for inst in all_instruments
            if isinstance(inst, dict) and inst.get('symbol') in TICKERS
        ]

        print(f"Fetched {len(relevant_data)} relevant instruments. MEP: {mep_rate}")

        result = {
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

        _data_cache['data'] = result
        _data_cache['timestamp'] = now
        return result
