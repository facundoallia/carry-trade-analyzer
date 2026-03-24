import { useState, useMemo } from 'react'

const SCENARIOS = [
  { label: 'MEP 1300', key: 'carry_1300', mep: 1300 },
  { label: 'MEP 1400', key: 'carry_1400', mep: 1400 },
  { label: 'MEP 1500', key: 'carry_1500', mep: 1500 },
  { label: 'MEP 1600', key: 'carry_1600', mep: 1600 },
  { label: 'MEP 1700', key: 'carry_1700', mep: 1700 },
  { label: 'MEP 1800', key: 'carry_1800', mep: 1800 },
  { label: 'Techo Banda', key: 'carry_techo', mep: null },
]

function fmtUSD(val) {
  return '$' + val.toFixed(2)
}

function fmtPct(val) {
  return (val * 100).toFixed(2) + '%'
}

export default function SimulationPanel({ carryData, mepRate }) {
  const [amount, setAmount] = useState('')
  const [selectedTicker, setSelectedTicker] = useState('')
  const [results, setResults] = useState(null)
  const [simError, setSimError] = useState(null)

  const canSimulate = amount > 0 && selectedTicker && mepRate && carryData.length > 0

  function runSimulation() {
    setSimError(null)
    const usd = parseFloat(amount)
    if (!usd || usd < 1) { setSimError('El monto debe ser mayor a 1 USD'); return }
    if (usd > 1_000_000) { setSimError('El monto debe ser menor a 1.000.000 USD'); return }
    if (!selectedTicker) { setSimError('Seleccione un bono'); return }
    if (!mepRate) { setSimError('MEP no disponible. Actualice los datos.'); return }

    const bond = carryData.find(b => b.ticker === selectedTicker)
    if (!bond) { setSimError('Bono no encontrado'); return }

    const pesosInverted = usd * mepRate
    const bondsQty = pesosInverted / bond.precio

    const validScenarios = SCENARIOS.filter(s => {
      const v = bond[s.key]
      return v !== '-' && v != null && typeof v === 'number' && isFinite(v)
    })

    if (validScenarios.length === 0) {
      setSimError('Todos los escenarios exceden el techo de la banda para este bono.')
      setResults(null)
      return
    }

    setResults({
      usd,
      pesosInverted,
      bondsQty,
      bond,
      scenarios: validScenarios,
    })
  }

  return (
    <section className="bg-white border border-gray-200">
      <div className="px-5 py-3 border-b border-gray-200">
        <h2 className="text-xl font-bold text-navy-700">Simulador de Inversión</h2>
      </div>

      <div className="p-5">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-gray-600">Monto en USD a invertir</label>
            <input
              type="number"
              min="1"
              step="1"
              placeholder="1000"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              className="border border-gray-300 px-3 py-2 text-sm w-44 focus:outline-none focus:ring-2 focus:ring-navy-700"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-gray-600">Seleccionar bono</label>
            <select
              value={selectedTicker}
              onChange={e => setSelectedTicker(e.target.value)}
              className="border border-gray-300 px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-navy-700"
            >
              <option value="">Seleccione un bono...</option>
              {carryData.map(b => (
                <option key={b.ticker} value={b.ticker}>
                  {b.ticker} — Vence: {b.fecha_vencimiento}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={runSimulation}
            disabled={!canSimulate}
            className="bg-navy-700 hover:bg-navy-600 disabled:opacity-40 disabled:cursor-not-allowed
                       text-white text-sm font-semibold px-5 py-2 transition-colors"
          >
            Simular Inversión
          </button>
        </div>

        {simError && (
          <p className="mt-3 text-sm text-red-600">{simError}</p>
        )}

        {results && (
          <div className="mt-5 overflow-x-auto animate-fade-in">
            <table className="w-full text-sm border border-gray-200">
              <thead>
                <tr className="bg-navy-700 text-white">
                  <th className="px-3 py-2 text-left font-semibold">Métrica</th>
                  {results.scenarios.map(s => (
                    <th key={s.key} className="px-3 py-2 text-center font-semibold whitespace-nowrap">
                      {s.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    label: 'MEP al vencimiento',
                    vals: results.scenarios.map(s => s.mep ? `$${s.mep}` : 'Techo'),
                  },
                  {
                    label: 'Rendimiento en USD (%)',
                    vals: results.scenarios.map(s => fmtPct(results.bond[s.key])),
                    highlight: true,
                  },
                  {
                    label: 'USD invertidos (hoy)',
                    vals: results.scenarios.map(() => fmtUSD(results.usd)),
                  },
                  {
                    label: 'Pesos invertidos (hoy)',
                    vals: results.scenarios.map(() => '$' + results.pesosInverted.toFixed(0)),
                  },
                  {
                    label: 'Cantidad de bonos',
                    vals: results.scenarios.map(() => results.bondsQty.toFixed(4)),
                  },
                  {
                    label: 'USD al vencimiento',
                    vals: results.scenarios.map(s => fmtUSD(results.usd * (1 + results.bond[s.key]))),
                    highlight: true,
                  },
                  {
                    label: 'Ganancia / Pérdida USD',
                    vals: results.scenarios.map(s => {
                      const gain = results.usd * results.bond[s.key]
                      return (gain >= 0 ? '+' : '') + fmtUSD(gain)
                    }),
                    highlight: true,
                  },
                ].map(({ label, vals, highlight }) => (
                  <tr key={label} className={highlight ? 'bg-blue-50' : ''}>
                    <td className="px-3 py-1.5 font-semibold text-gray-700 whitespace-nowrap border-b border-gray-100">
                      {label}
                    </td>
                    {vals.map((v, i) => (
                      <td key={i} className="px-3 py-1.5 text-center tabular-nums border-b border-gray-100">
                        {v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
