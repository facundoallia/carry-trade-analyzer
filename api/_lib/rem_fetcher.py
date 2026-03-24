"""
REM Data Fetcher — proyecciones de inflación del REM BCRA
Adaptado para Vercel serverless: cache en memoria + /tmp (sin disco del proyecto)

Cache Strategy:
- Days 1-10: TTL = 12 horas (captura actualizaciones del REM)
- Days 11+: TTL = hasta fin de mes (datos estables)
"""
import requests
import json
import os
import warnings
from typing import Dict, List, Optional
from datetime import date, datetime
from calendar import monthrange

from config import REM_IPC_ENDPOINT, LAST_KNOWN_INFLATION

from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Cache en memoria a nivel de módulo
_memory_cache: Optional[Dict] = None
_memory_cache_month: Optional[str] = None

TMP_CACHE_FILE = '/tmp/rem_ipc_data.json'


class REMDataFetcher:
    """Fetch inflation projections from REM BCRA API with adaptive cache"""

    def __init__(self):
        self.timeout = 3

    def _get_current_month_key(self) -> str:
        return date.today().strftime('%Y-%m')

    def _get_cache_ttl_hours(self) -> int:
        today = date.today()
        if today.day <= 10:
            return 12
        last_day = monthrange(today.year, today.month)[1]
        days_remaining = last_day - today.day
        return days_remaining * 24 + 12

    def _is_cache_expired(self, cache_timestamp_str: str) -> bool:
        try:
            cache_time = datetime.fromisoformat(cache_timestamp_str)
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            ttl_hours = self._get_cache_ttl_hours()
            return age_hours > ttl_hours
        except Exception:
            return True

    def _load_tmp_cache(self) -> Optional[Dict]:
        """Carga cache desde /tmp si existe y es válido"""
        if not os.path.exists(TMP_CACHE_FILE):
            return None
        try:
            with open(TMP_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            if not isinstance(cache_data, dict):
                return None
            if cache_data.get('month_key') != self._get_current_month_key():
                return None
            if self._is_cache_expired(cache_data.get('timestamp', '')):
                return None
            print(f"[OK] Using /tmp REM cache from {cache_data.get('timestamp', 'unknown')}")
            return cache_data.get('data')
        except Exception as e:
            print(f"Error loading /tmp REM cache: {e}")
            return None

    def _save_tmp_cache(self, data: Dict) -> None:
        try:
            cache_data = {
                'month_key': self._get_current_month_key(),
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(TMP_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            print(f"[OK] REM data cached to /tmp")
        except Exception as e:
            print(f"Warning: Could not save /tmp REM cache: {e}")

    def fetch_ipc_projections(self, force_refresh: bool = False) -> Optional[Dict]:
        """Obtiene proyecciones IPC del REM con cache adaptivo"""
        global _memory_cache, _memory_cache_month
        current_month = self._get_current_month_key()

        # 1. Cache en memoria
        if not force_refresh and _memory_cache_month == current_month and _memory_cache is not None:
            return _memory_cache

        # 2. Cache en /tmp
        if not force_refresh:
            tmp_data = self._load_tmp_cache()
            if tmp_data is not None:
                _memory_cache = tmp_data
                _memory_cache_month = current_month
                return tmp_data

        # 3. Fetch fresco de la API
        print(f"Fetching fresh REM data... (force_refresh={force_refresh})")
        try:
            response = requests.get(REM_IPC_ENDPOINT, timeout=self.timeout, verify=False)
            response.raise_for_status()
            data = response.json()
            _memory_cache = data
            _memory_cache_month = current_month
            self._save_tmp_cache(data)
            return data
        except Exception as e:
            print(f"Error fetching REM IPC data: {e}")
            if _memory_cache is not None:
                print("[WARN] Using expired in-memory cache as fallback")
                return _memory_cache
            try:
                tmp_data = self._load_tmp_cache_expired()
                if tmp_data:
                    print("[WARN] Using expired /tmp cache as fallback")
                    return tmp_data
            except Exception:
                pass
            return None

    def _load_tmp_cache_expired(self) -> Optional[Dict]:
        """Carga cache /tmp ignorando expiración (fallback de último recurso)"""
        if not os.path.exists(TMP_CACHE_FILE):
            return None
        try:
            with open(TMP_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            return cache_data.get('data')
        except Exception:
            return None

    def _get_annual_projection(self, target_date: date, rem_data: Dict) -> Optional[float]:
        try:
            today = date.today()
            months_ahead = (target_date.year - today.year) * 12 + (target_date.month - today.month)
            for row in rem_data['datos']:
                periodo = str(row.get('período', '')).lower()
                if str(target_date.year) == periodo.strip():
                    mediana = row.get('mediana')
                    if mediana:
                        return float(mediana) / 100
            for row in rem_data['datos']:
                periodo = str(row.get('período', '')).lower()
                if months_ahead <= 12 and 'próx. 12 meses' in periodo:
                    mediana = row.get('mediana')
                    if mediana:
                        return float(mediana) / 100
                elif months_ahead > 12 and months_ahead <= 24 and 'próx. 24 meses' in periodo:
                    mediana = row.get('mediana')
                    if mediana:
                        return float(mediana) / 100
            return None
        except Exception:
            return None

    def _parse_period_to_date(self, periodo_str: str) -> Optional[date]:
        try:
            if '-' in periodo_str and len(periodo_str) > 10:
                try:
                    dt = datetime.strptime(periodo_str.strip(), '%Y-%m-%d %H:%M:%S')
                    return date(dt.year, dt.month, 1)
                except Exception:
                    pass
            meses = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
                'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            periodo_lower = periodo_str.lower()
            for mes_str, mes_num in meses.items():
                if mes_str in periodo_lower:
                    year_match = None
                    for char_idx in range(len(periodo_str) - 1):
                        if periodo_str[char_idx:char_idx+2].isdigit():
                            year_match = int(periodo_str[char_idx:char_idx+2])
                            break
                    if year_match is not None:
                        year = 2000 + year_match if year_match < 100 else year_match
                        return date(year, mes_num, 1)
            return None
        except Exception:
            return None
