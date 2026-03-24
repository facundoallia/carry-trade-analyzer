"""
Vercel serverless handler: GET /api/chart-data
Retorna datos del gráfico Breakeven vs Techo de Banda
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))

from http.server import BaseHTTPRequestHandler
from carry_calculator import CarryTradeCalculator

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
            chart_data = calc.get_chart_data()
            result = {'chart_data': chart_data}
            status = 200
        except Exception as e:
            result = {'error': str(e), 'chart_data': {}}
            status = 500
            print(f"[ERROR] chart-data handler: {e}")

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
        pass
