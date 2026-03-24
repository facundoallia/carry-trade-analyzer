"""
Vercel serverless handler: GET /api/rem-data
Retorna proyecciones de inflación del REM BCRA para la sección de metodología
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))

from http.server import BaseHTTPRequestHandler
from rem_fetcher import REMDataFetcher

_rem_fetcher = None


def get_fetcher():
    global _rem_fetcher
    if _rem_fetcher is None:
        _rem_fetcher = REMDataFetcher()
    return _rem_fetcher


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            fetcher = get_fetcher()
            rem_data = fetcher.fetch_ipc_projections()

            if not rem_data or 'datos' not in rem_data:
                body = json.dumps({'status': 'error', 'message': 'Sin datos REM disponibles'})
                self._respond(503, body)
                return

            # Separar proyecciones mensuales (tienen fecha parseable) de anuales
            monthly_projections = []
            annual_projections = []

            for row in rem_data.get('datos', []):
                periodo = row.get('período', '')
                mediana = row.get('mediana', row.get('Mediana'))
                if not mediana:
                    continue

                parsed_date = fetcher._parse_period_to_date(str(periodo))
                if parsed_date:
                    monthly_projections.append({
                        'periodo': parsed_date.strftime('%Y-%m'),
                        'mediana': float(mediana),
                        'participantes': row.get('participantes', None)
                    })
                else:
                    # Proyección anual o multi-año
                    periodo_str = str(periodo).strip()
                    if periodo_str.isdigit() or 'próx.' in periodo_str.lower():
                        annual_projections.append({
                            'periodo': periodo_str,
                            'mediana': float(mediana)
                        })

            result = {
                'status': 'success',
                'monthly_projections': monthly_projections[:12],  # Máximo 12 meses
                'annual_projections': annual_projections[:4],
                'metadata': rem_data.get('metadata', {})
            }
            body = json.dumps(result)
            self._respond(200, body)

        except Exception as e:
            body = json.dumps({'status': 'error', 'message': str(e)})
            self._respond(500, body)
            print(f"[ERROR] rem-data handler: {e}")

    def _respond(self, status: int, body: str):
        self.send_response(status)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass
