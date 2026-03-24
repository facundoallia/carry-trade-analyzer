import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

const ENDPOINTS = [
  { path: '/api/metadata',         desc: 'Información sobre última actualización' },
  { path: '/api/ipc_general',      desc: 'Inflación general (IPC)' },
  { path: '/api/ipc_nucleo',       desc: 'Inflación núcleo' },
  { path: '/api/tipo_cambio',      desc: 'Tipo de cambio nominal (USD/ARS)' },
  { path: '/api/tasa_interes',     desc: 'Tasa de interés (TAMAR)' },
  { path: '/api/pbi',              desc: 'PIB a precios constantes' },
  { path: '/api/exportaciones',    desc: 'Exportaciones' },
  { path: '/api/importaciones',    desc: 'Importaciones' },
  { path: '/api/desocupacion',     desc: 'Tasa de desocupación' },
  { path: '/api/resultado_primario', desc: 'Resultado primario SPNF' },
  { path: '/api/bloques',          desc: 'Índice maestro de todas las tablas' },
]

const PIPELINE_STEPS = [
  {
    num: '1',
    title: 'Descarga automática',
    text: 'GitHub Actions descarga el archivo Excel del REM desde bcra.gob.ar (días 1-15 de cada mes)'
  },
  {
    num: '2',
    title: 'Procesamiento',
    text: 'Python + Pandas parsea, normaliza y estructura 19 tablas JSON con medianas, percentiles y proyecciones de ~45 economistas'
  },
  {
    num: '3',
    title: 'Distribución',
    text: 'Los datos se almacenan en Cloudflare R2 y se sirven globalmente via Cloudflare Workers con cache de 1 hora'
  },
]

const BASE_URL = 'https://bcra-rem-api.facujallia.workers.dev'

export default function ApiSection() {
  const [open, setOpen] = useState(false)

  return (
    <section className="bg-white border border-gray-200">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors"
      >
        <h2 className="text-xl font-bold text-navy-700">
          API REM — BCRA (Datos Abiertos)
        </h2>
        {open ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
      </button>

      {open && (
        <div className="px-5 pb-6 border-t border-gray-100 animate-fade-in">
          <div className="space-y-5 mt-4">

            <p className="text-sm text-gray-600 leading-relaxed">
              Los datos de inflación proyectada provienen de la <strong>API REM — BCRA</strong>, un proyecto
              open-source que automatiza la lectura, normalización y distribución del Relevamiento de
              Expectativas de Mercado del Banco Central.
            </p>

            <div>
              <h3 className="font-semibold text-navy-700 mb-3">Pipeline de datos</h3>
              <div className="flex flex-col md:flex-row gap-4">
                {PIPELINE_STEPS.map(({ num, title, text }) => (
                  <div key={num} className="flex gap-3 flex-1 bg-blue-50 border border-blue-100 p-4">
                    <span className="flex-shrink-0 w-7 h-7 rounded-full bg-navy-700 text-white text-sm font-bold flex items-center justify-center">
                      {num}
                    </span>
                    <div>
                      <p className="font-semibold text-sm text-navy-700 mb-1">{title}</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-navy-700 mb-2">Endpoints disponibles</h3>
              <div className="overflow-x-auto">
                <table className="text-sm border border-gray-200 w-full">
                  <thead>
                    <tr className="bg-gray-100 text-gray-700">
                      <th className="px-3 py-2 text-left font-semibold">Endpoint</th>
                      <th className="px-3 py-2 text-left font-semibold">Descripción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ENDPOINTS.map(({ path, desc }, i) => (
                      <tr key={path} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-3 py-1.5 font-mono text-xs text-navy-700">{path}</td>
                        <td className="px-3 py-1.5 text-gray-600">{desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-400 mt-1.5">
                Cada tabla tiene además su versión <code className="text-navy-700">_top10</code> con
                los pronósticos individuales de los 10 mejores pronosticadores.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-navy-700 mb-2">Ejemplo de uso</h3>
              <pre className="bg-gray-900 text-green-300 text-xs p-4 overflow-x-auto leading-relaxed">
{`// JavaScript
fetch('${BASE_URL}/api/ipc_general')
  .then(r => r.json())
  .then(data => console.log(data.datos));

# Python
import requests
data = requests.get('${BASE_URL}/api/tipo_cambio').json()`}
              </pre>
            </div>

            <div className="text-sm text-gray-600 space-y-1">
              <p><strong>Base URL:</strong> <code className="text-navy-700">{BASE_URL}</code></p>
              <p>
                <strong>Código fuente:</strong>{' '}
                <a
                  href="https://github.com/facundoallia/rem-bcra-api"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  github.com/facundoallia/rem-bcra-api
                </a>
              </p>
              <p><strong>Acceso:</strong> API pública, sin autenticación. Rate limit: 1 req/min por IP.</p>
              <p><strong>Tecnologías:</strong> GitHub Actions → Python + Pandas → Cloudflare R2 → Cloudflare Workers</p>
            </div>

          </div>
        </div>
      )}
    </section>
  )
}
