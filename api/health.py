"""
Vercel serverless handler: GET /api/health
Health check del sistema
"""
import sys
import os
import json
from datetime import datetime

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

    def do_GET(self):
        try:
            calc = get_calculator()
            mep_rate = calc.get_mep_rate()
            result = {
                'status': 'ok',
                'mep_rate': mep_rate,
                'timestamp': datetime.now().isoformat(),
                'runtime': 'vercel-serverless-python'
            }
            status = 200
        except Exception as e:
            result = {'status': 'error', 'error': str(e)}
            status = 500

        body = json.dumps(result)
        self.send_response(status)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass
