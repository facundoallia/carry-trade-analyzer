const COLUMNS = [
  { key: 'ticker',            label: 'Ticker',       tip: 'Código identificatorio del bono o letra del Tesoro Nacional.' },
  { key: 'precio',            label: 'Precio',       tip: 'Precio actual del bono en pesos argentinos. Es el valor al cual se puede comprar hoy.' },
  { key: 'fecha_vencimiento', label: 'Vencimiento',  tip: 'Fecha en la cual el bono paga su valor nominal (100 pesos por cada bono).' },
  { key: 'dias_vencimiento',  label: 'Días',         tip: 'Cantidad de días que faltan desde hoy hasta la fecha de vencimiento del bono.' },
  { key: 'tem',               label: 'TEM',          tip: 'Tasa Efectiva Mensual — rendimiento mensual efectivo del bono en pesos.' },
  { key: 'tna',               label: 'TNA',          tip: 'Tasa Nominal Anual — tasa anual nominal simple (TEM × 12, sin capitalización).' },
  { key: 'tea',               label: 'TEA',          tip: 'Tasa Efectiva Anual — rendimiento anual efectivo con capitalización compuesta.' },
  { key: 'carry_1300',        label: 'Carry 1300',   tip: 'Rendimiento en USD si el MEP está a $1300 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_1400',        label: 'Carry 1400',   tip: 'Rendimiento en USD si el MEP está a $1400 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_1500',        label: 'Carry 1500',   tip: 'Rendimiento en USD si el MEP está a $1500 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_1600',        label: 'Carry 1600',   tip: 'Rendimiento en USD si el MEP está a $1600 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_1700',        label: 'Carry 1700',   tip: 'Rendimiento en USD si el MEP está a $1700 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_1800',        label: 'Carry 1800',   tip: 'Rendimiento en USD si el MEP está a $1800 al vencimiento. Muestra "-" si excede el techo de la banda.' },
  { key: 'carry_techo',       label: 'Carry Techo',  tip: 'Rendimiento en USD con MEP al techo de la banda cambiaria — escenario más conservador (peor caso).' },
]

const CARRY_KEYS = ['carry_1300', 'carry_1400', 'carry_1500', 'carry_1600', 'carry_1700', 'carry_1800', 'carry_techo']
const RATE_KEYS = ['tem', 'tna', 'tea']

function getCarryClass(value) {
  if (value === '-' || value == null || typeof value !== 'number' || !isFinite(value)) return ''
  if (value > 0.02) {
    const intensity = Math.min(5, Math.floor(Math.min(1, value / 0.15) * 5) + 1)
    return `carry-pos-${intensity}`
  }
  if (value > -0.05) return 'carry-neutral'
  if (value > -0.11) return 'carry-neg-1'
  const intensity = Math.min(3, Math.floor(Math.min(1, Math.abs(value + 0.11) / 0.15) * 3) + 1)
  return `carry-neg-${intensity + 1}`
}

function fmt(key, value) {
  if (value === '-' || value == null) return '—'
  if (CARRY_KEYS.includes(key) || RATE_KEYS.includes(key)) {
    if (typeof value !== 'number' || !isFinite(value)) return '—'
    return (value * 100).toFixed(1) + '%'
  }
  if (key === 'precio') return '$' + Number(value).toFixed(2)
  return String(value)
}

function ThWithTooltip({ label, tip }) {
  return (
    <th className="th-tooltip px-3 py-2 text-left text-xs font-semibold text-white whitespace-nowrap select-none">
      {label}
      <span className="tooltip-content">{tip}</span>
    </th>
  )
}

export default function CarryTable({ data, loading, error }) {
  return (
    <section className="bg-white border border-gray-200">
      <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-xl font-bold text-navy-700">Matriz de Rendimientos por Escenario</h2>
        {loading && (
          <span className="flex items-center gap-2 text-sm text-gray-400">
            <span className="inline-block w-4 h-4 border-2 border-navy-700 border-t-transparent rounded-full animate-spin" />
            Actualizando...
          </span>
        )}
      </div>

      {error && (
        <div className="px-5 py-3 bg-red-50 text-red-700 text-sm border-b border-red-100">
          {error}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-navy-700">
              {COLUMNS.map(col => (
                <ThWithTooltip key={col.key} label={col.label} tip={col.tip} />
              ))}
            </tr>
          </thead>
          <tbody id="carry-table-body">
            {!loading && data.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} className="text-center py-10 text-gray-400">
                  No hay datos disponibles
                </td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr
                  key={row.ticker}
                  className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} animate-fade-in`}
                >
                  <td className="px-3 py-1.5 font-semibold text-navy-700 whitespace-nowrap">
                    {row.ticker}
                  </td>
                  <td className="px-3 py-1.5 tabular-nums">{fmt('precio', row.precio)}</td>
                  <td className="px-3 py-1.5 whitespace-nowrap">{row.fecha_vencimiento}</td>
                  <td className="px-3 py-1.5 tabular-nums">{row.dias_vencimiento}</td>
                  <td className="px-3 py-1.5 tabular-nums">{fmt('tem', row.tem)}</td>
                  <td className="px-3 py-1.5 tabular-nums">{fmt('tna', row.tna)}</td>
                  <td className="px-3 py-1.5 tabular-nums">{fmt('tea', row.tea)}</td>
                  {CARRY_KEYS.map(k => (
                    <td
                      key={k}
                      className={`px-3 py-1.5 text-center tabular-nums font-medium ${getCarryClass(row[k])}`}
                    >
                      {fmt(k, row[k])}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
