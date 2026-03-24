"""
Vercel serverless handler: GET /api/carry-data
Retorna tabla de carry trade + color limits + MEP rate
"""
import sys
import os
import json

# Agregar _lib al path de Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))

from http.server import BaseHTTPRequestHandler
from carry_calculator import CarryTradeCalculator

# Calculator a nivel de módulo (reutilizado en warm requests)
_calculator = None


def get_calculator():
    global _calculator
    if _calculator is None:
        _calculator = CarryTradeCalculator()
    return _calculator


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            calc = get_calculator()
            # Reutiliza cache interno del DataFetcher (30s TTL)
            table_data = calc.get_table_data()
            color_limits = calc.get_color_limits()
            mep_rate = calc.get_mep_rate()

            result = {
                'data': table_data,
                'color_limits': color_limits,
                'mep_rate': mep_rate,
            }
            status = 200
        except Exception as e:
            result = {'error': str(e), 'data': [], 'mep_rate': None, 'color_limits': {}}
            status = 500
            print(f"[ERROR] carry-data handler: {e}")

        body = json.dumps(result)
        self.send_response(status)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        pass  # Suprimir logs de acceso
