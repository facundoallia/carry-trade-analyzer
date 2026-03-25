import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function periodLabel(periodo) {
  const parts = periodo.split('-')
  if (parts.length === 2) {
    const mes = MESES[parseInt(parts[1]) - 1] || parts[1]
    return `${mes} ${parts[0]}`
  }
  return periodo
}

export default function RemSection({ remData }) {
  const [open, setOpen] = useState(false)

  const monthly = remData?.monthly_projections || []
  const annual = remData?.annual_projections || []
  const meta = remData?.metadata || {}

  const metaDate = meta.ultima_actualizacion
    ? new Date(meta.ultima_actualizacion).toLocaleDateString('es-AR')
    : null

  return (
    <section className="bg-white border border-gray-200">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors"
      >
        <h2 className="text-xl font-bold text-navy-700">
          Metodología: Estimación de Bandas Cambiarias
        </h2>
        {open ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
      </button>

      {open && (
        <div className="px-5 pb-6 border-t border-gray-100 animate-fade-in">
          <div className="space-y-5 mt-4">

            <div>
              <h3 className="font-semibold text-navy-700 mb-2">¿Cómo se estiman las bandas?</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Las bandas cambiarias evolucionan diariamente según la <strong>inflación T-2</strong> (dos meses atrás),
                utilizando datos reales del INDEC cuando están disponibles y proyecciones del REM para meses futuros.
              </p>
            </div>

            <div className="bg-gray-50 border border-gray-200 p-4">
              <h4 className="font-semibold text-gray-700 mb-2">Fórmula de evolución diaria</h4>
              <code className="text-sm text-navy-700 block mb-1">
                Banda<sub>día</sub> = Banda<sub>día-1</sub> × (1 + tasa_diaria)
              </code>
              <code className="text-sm text-navy-700 block">
                tasa_diaria = (1 + inflación_mensual_T-2)<sup>1/días_del_mes</sup> − 1
              </code>
              <p className="text-xs text-gray-500 mt-2">
                La inflación T-2 corresponde a la inflación de <strong>dos meses atrás</strong>. Ej: la banda de marzo 2026
                evoluciona según la inflación de enero 2026.
              </p>
            </div>

            <div>
              <div className="flex items-baseline justify-between mb-2">
                <h3 className="font-semibold text-navy-700">Proyecciones REM — IPC General (mediana)</h3>
                {metaDate && (
                  <span className="text-xs text-gray-400">
                    Actualizado: {metaDate} · {monthly[0]?.participantes || '~45'} participantes
                  </span>
                )}
              </div>

              {monthly.length > 0 || annual.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="text-sm border border-gray-200">
                    <thead>
                      <tr className="bg-navy-700 text-white">
                        <th className="px-3 py-2 text-left font-semibold whitespace-nowrap">Indicador</th>
                        {monthly.map(m => (
                          <th key={m.periodo} className="px-3 py-2 text-center font-semibold whitespace-nowrap">
                            {periodLabel(m.periodo)}
                          </th>
                        ))}
                        {annual.map(a => (
                          <th key={a.periodo} className="px-3 py-2 text-center font-semibold whitespace-nowrap">
                            {a.periodo.length === 4 ? `Anual ${a.periodo}` : a.periodo}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="bg-blue-50">
                        <td className="px-3 py-2 font-semibold text-gray-700">Mediana (%)</td>
                        {monthly.map(m => (
                          <td key={m.periodo} className="px-3 py-2 text-center tabular-nums">
                            {Number(m.mediana).toFixed(2)}%
                          </td>
                        ))}
                        {annual.map(a => (
                          <td key={a.periodo} className="px-3 py-2 text-center tabular-nums font-semibold">
                            {Number(a.mediana).toFixed(2)}%
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Cargando proyecciones del REM...</p>
              )}
            </div>

            <div>
              <h3 className="font-semibold text-navy-700 mb-2">Prioridad de datos para la banda</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                <li><strong>Datos reales INDEC</strong> — Se priorizan siempre sobre cualquier proyección</li>
                <li><strong>Proyecciones mensuales REM</strong> — Mediana de ~45 economistas profesionales</li>
                <li><strong>Calibración con proyección anual REM</strong> — Para meses sin dato mensual específico</li>
                <li><strong>Fallback conservador (2,0%)</strong> — Solo si no hay ningún dato disponible</li>
              </ol>
            </div>

          </div>
        </div>
      )}
    </section>
  )
}
