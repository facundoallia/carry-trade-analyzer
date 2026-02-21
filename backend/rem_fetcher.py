"""
REM Data Fetcher - Obtiene proyecciones de inflación del REM BCRA
Con cache persistente adaptivo para optimizar llamadas a la API

Cache Strategy:
- Days 1-10 of month: TTL = 12 hours (captures REM updates)
- Days 11+ of month: TTL = rest of month (data is stable)
"""

import requests
import json
import os
import warnings
from typing import Dict, List, Optional
from datetime import date, datetime
from pathlib import Path
from calendar import monthrange
from backend.config import REM_IPC_ENDPOINT, LAST_KNOWN_INFLATION

# Disable SSL warnings (only for development - CloudFlare Workers SSL cert issue)
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

class REMDataFetcher:
    """Fetch inflation projections from REM BCRA API with persistent monthly cache"""

    def __init__(self, cache_dir: Optional[str] = None):
        self.timeout = 3  # Reduced from 10 to 3 seconds for faster failure

        # Setup persistent cache directory
        if cache_dir is None:
            # Use .cache directory in project root
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / ".cache"
        else:
            cache_dir = Path(cache_dir)

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.cache_file = self.cache_dir / "rem_ipc_data.json"

        # In-memory cache for current session (faster access)
        self._memory_cache = None
        self._memory_cache_month = None

    def _get_current_month_key(self) -> str:
        """Get cache key for current month (YYYY-MM)"""
        return date.today().strftime('%Y-%m')

    def _get_cache_ttl_hours(self) -> int:
        """
        Get cache TTL (time to live) in hours based on day of month

        REM API updates between day 1-10 of each month (variable date).
        Strategy:
        - Days 1-10: TTL = 12 hours (allows 2 checks/day to catch update)
        - Days 11-31: TTL = until end of month (data won't change)

        Returns:
            Hours until cache should be considered stale
        """
        today = date.today()
        day_of_month = today.day

        if day_of_month <= 10:
            # During update window: short TTL to catch changes
            return 12
        else:
            # After update window: long TTL until month end
            # Calculate hours remaining in month
            last_day = monthrange(today.year, today.month)[1]
            days_remaining = last_day - day_of_month
            return days_remaining * 24 + 12  # Extra 12h buffer

    def _is_cache_expired(self, cache_timestamp_str: str) -> bool:
        """
        Check if cache is expired based on adaptive TTL

        Args:
            cache_timestamp_str: ISO format timestamp string

        Returns:
            True if cache is expired
        """
        try:
            cache_time = datetime.fromisoformat(cache_timestamp_str)
            now = datetime.now()

            # Calculate age in hours
            age_hours = (now - cache_time).total_seconds() / 3600

            # Get current TTL
            ttl_hours = self._get_cache_ttl_hours()

            is_expired = age_hours > ttl_hours

            if is_expired:
                print(f"Cache expired: {age_hours:.1f}h old (TTL: {ttl_hours}h)")
            else:
                print(f"Cache valid: {age_hours:.1f}h old (TTL: {ttl_hours}h)")

            return is_expired

        except Exception as e:
            print(f"Error checking cache expiration: {e}")
            return True  # If error, consider expired

    def _load_cache_from_disk(self) -> Optional[Dict]:
        """Load cache from disk if it exists and is valid (month + TTL check)"""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Validate cache structure
            if not isinstance(cache_data, dict):
                print("Invalid cache structure, ignoring")
                return None

            cached_month = cache_data.get('month_key')
            current_month = self._get_current_month_key()

            # First check: same month
            if cached_month != current_month:
                print(f"Cache expired (different month: cached={cached_month}, current={current_month})")
                return None

            # Second check: TTL based on day of month
            timestamp = cache_data.get('timestamp')
            if self._is_cache_expired(timestamp):
                print(f"Cache expired (TTL exceeded)")
                return None

            print(f"[OK] Using cached REM data from {cache_data.get('timestamp', 'unknown')}")
            return cache_data.get('data')

        except Exception as e:
            print(f"Error loading cache from disk: {e}")
            return None

    def _save_cache_to_disk(self, data: Dict) -> None:
        """Save REM data to disk with metadata"""
        try:
            cache_data = {
                'month_key': self._get_current_month_key(),
                'timestamp': datetime.now().isoformat(),
                'data': data
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            print(f"[OK] REM data cached to disk for month {cache_data['month_key']}")

        except Exception as e:
            print(f"Warning: Could not save cache to disk: {e}")

    def fetch_ipc_projections(self, force_refresh: bool = False) -> Optional[Dict]:
        """
        Obtiene proyecciones de IPC del REM con caché persistente mensual

        Los datos del REM se actualizan mensualmente, por lo que usamos un cache
        que se invalida automáticamente al cambiar el mes.

        Args:
            force_refresh: Si es True, ignora el cache y hace request nuevo

        Returns:
            Dict con proyecciones de inflación mensual
        """
        current_month = self._get_current_month_key()

        # 1. Check in-memory cache first (fastest)
        if not force_refresh and self._memory_cache_month == current_month and self._memory_cache is not None:
            return self._memory_cache

        # 2. Check disk cache (valid for current month)
        if not force_refresh:
            disk_cache = self._load_cache_from_disk()
            if disk_cache is not None:
                # Update in-memory cache
                self._memory_cache = disk_cache
                self._memory_cache_month = current_month
                return disk_cache

        # 3. Fetch fresh data from API
        print(f"Fetching fresh REM data from API... (force_refresh={force_refresh})")
        try:
            # Note: verify=False is a workaround for CloudFlare Workers SSL cert issue
            # when system date is in future (2026). Remove in production if cert is fixed.
            response = requests.get(REM_IPC_ENDPOINT, timeout=self.timeout, verify=False)
            response.raise_for_status()
            data = response.json()

            # Save to both caches
            self._memory_cache = data
            self._memory_cache_month = current_month
            self._save_cache_to_disk(data)

            return data

        except Exception as e:
            print(f"Error fetching REM IPC data: {e}")

            # Fallback: try to use any existing cache (even if expired)
            if self._memory_cache is not None:
                print("[WARN] Using expired in-memory cache as fallback")
                return self._memory_cache

            # Try to load expired disk cache
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    data = cache_data.get('data')
                    if data:
                        print(f"[WARN] Using expired disk cache from {cache_data.get('month_key')} as fallback")
                        return data
                except:
                    pass

            return None

    def clear_cache(self) -> None:
        """Clear both in-memory and disk cache"""
        self._memory_cache = None
        self._memory_cache_month = None

        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                print("[OK] Cache cleared successfully")
            except Exception as e:
                print(f"Error clearing disk cache: {e}")

    def get_cache_info(self) -> Dict:
        """Get information about current cache status"""
        info = {
            'memory_cache_active': self._memory_cache is not None,
            'memory_cache_month': self._memory_cache_month,
            'disk_cache_exists': self.cache_file.exists(),
            'current_month': self._get_current_month_key()
        }

        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                info['disk_cache_month'] = cache_data.get('month_key')
                info['disk_cache_timestamp'] = cache_data.get('timestamp')
                info['disk_cache_valid'] = cache_data.get('month_key') == self._get_current_month_key()
            except:
                pass

        return info

    def get_inflation_projection(self, target_date: date) -> float:
        """
        Obtiene proyección de inflación para un mes específico
        Si no hay dato mensual específico, usa proyecciones anuales (12 y 24 meses) prorrateadas

        Args:
            target_date: Fecha para la cual se busca la proyección

        Returns:
            Tasa de inflación mensual proyectada (ej: 0.025 para 2.5%)
        """
        # Obtener datos del REM
        rem_data = self.fetch_ipc_projections()

        if not rem_data or 'datos' not in rem_data:
            # Fallback: usar último dato conocido
            return LAST_KNOWN_INFLATION['rate']

        # Buscar proyección para el mes objetivo
        target_period = target_date.strftime('%Y-%m')

        for row in rem_data['datos']:
            periodo = row.get('período', '')

            # Intentar parsear el período (puede venir en diferentes formatos)
            try:
                # Formato esperado: "2025-12", "Dic-25", etc.
                if target_period in periodo or self._match_period(periodo, target_date):
                    # Obtener mediana de proyección
                    mediana = row.get('mediana', row.get('Mediana'))
                    if mediana:
                        # Convertir de porcentaje a decimal
                        return float(mediana) / 100
            except:
                continue

        # Si no encontramos proyección mensual, usar proyecciones anuales prorrateadas
        annual_rate = self._get_annual_projection(target_date, rem_data)
        if annual_rate is not None:
            # Convertir tasa anual a mensual: (1 + anual)^(1/12) - 1
            monthly_rate = ((1 + annual_rate) ** (1/12)) - 1
            return monthly_rate

        # Si no encontramos nada, usar último dato conocido
        return LAST_KNOWN_INFLATION['rate']

    def _get_annual_projection(self, target_date: date, rem_data: Dict) -> Optional[float]:
        """
        Obtiene proyección anual prorrateada para fechas sin dato mensual
        Usa "próx. 12 meses" o "próx. 24 meses" según corresponda
        O proyecciones por año (2026, 2027, etc.)

        Args:
            target_date: Fecha objetivo
            rem_data: Datos del REM

        Returns:
            Tasa anual como decimal o None
        """
        try:
            # Calcular meses desde hoy hasta target_date
            today = date.today()
            months_ahead = (target_date.year - today.year) * 12 + (target_date.month - today.month)

            # Primero buscar por año específico (2026, 2027, etc.)
            for row in rem_data['datos']:
                periodo = str(row.get('período', '')).lower()

                # Match directo por año
                if str(target_date.year) == periodo.strip():
                    mediana = row.get('mediana')
                    if mediana:
                        annual_rate = float(mediana) / 100
                        return annual_rate

            # Si no hay proyección específica del año, usar próx. 12/24 meses
            for row in rem_data['datos']:
                periodo = str(row.get('período', '')).lower()

                if months_ahead <= 12 and 'próx. 12 meses' in periodo:
                    mediana = row.get('mediana')
                    if mediana:
                        annual_rate = float(mediana) / 100
                        return annual_rate

                elif months_ahead > 12 and months_ahead <= 24 and 'próx. 24 meses' in periodo:
                    mediana = row.get('mediana')
                    if mediana:
                        annual_rate = float(mediana) / 100
                        return annual_rate

            return None
        except Exception as e:
            return None

    def _match_period(self, periodo_str: str, target_date: date) -> bool:
        """
        Intenta hacer match entre el período del REM y la fecha objetivo

        Args:
            periodo_str: String del período del REM
            target_date: Fecha objetivo

        Returns:
            True si coinciden
        """
        try:
            # Mapeo de meses en español
            meses = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
                'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }

            periodo_lower = periodo_str.lower()

            # Buscar mes en el string
            for mes_str, mes_num in meses.items():
                if mes_str in periodo_lower:
                    # Buscar año (últimos 2 dígitos)
                    year_match = None
                    for char_idx in range(len(periodo_str) - 1):
                        if periodo_str[char_idx:char_idx+2].isdigit():
                            year_match = int(periodo_str[char_idx:char_idx+2])
                            break

                    if year_match:
                        year = 2000 + year_match if year_match < 100 else year_match
                        return target_date.year == year and target_date.month == mes_num

            return False
        except:
            return False

    def _parse_period_to_date(self, periodo_str: str) -> Optional[date]:
        """
        Parsea un string de período del REM a un objeto date

        Ejemplos: "2026-01-31 00:00:00" -> date(2026, 1, 1)
                 "Dic-25" -> date(2025, 12, 1)
                 "Ene-26" -> date(2026, 1, 1)
                 "2026" -> None (solo años, no meses específicos)

        Returns:
            date object o None si no se puede parsear
        """
        try:
            # Intentar parsear formato datetime completo "YYYY-MM-DD HH:MM:SS"
            if '-' in periodo_str and len(periodo_str) > 10:
                try:
                    # Formato: "2026-01-31 00:00:00"
                    dt = datetime.strptime(periodo_str.strip(), '%Y-%m-%d %H:%M:%S')
                    return date(dt.year, dt.month, 1)
                except:
                    pass

            # Mapeo de meses en español (fallback para formatos viejos)
            meses = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
                'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }

            periodo_lower = periodo_str.lower()

            # Buscar mes en el string
            for mes_str, mes_num in meses.items():
                if mes_str in periodo_lower:
                    # Buscar año (últimos 2 dígitos)
                    year_match = None
                    for char_idx in range(len(periodo_str) - 1):
                        if periodo_str[char_idx:char_idx+2].isdigit():
                            year_match = int(periodo_str[char_idx:char_idx+2])
                            break

                    if year_match is not None:
                        year = 2000 + year_match if year_match < 100 else year_match
                        return date(year, mes_num, 1)

            return None
        except:
            return None

    def get_inflation_series(self, start_date: date, end_date: date) -> Dict[date, float]:
        """
        Obtiene serie de proyecciones de inflación

        Args:
            start_date: Fecha inicial
            end_date: Fecha final

        Returns:
            Diccionario {fecha: tasa_inflacion}
        """
        inflation_series = {}

        current = start_date
        while current <= end_date:
            inflation_series[current] = self.get_inflation_projection(current)

            # Avanzar al siguiente mes
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return inflation_series
