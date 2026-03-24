const CARDS = [
  {
    icon: '🎯',
    title: 'Concepto del Carry Trade',
    text: 'Consiste en capturar el diferencial entre las altas tasas en pesos argentinos y las bajas tasas en dólares, esperando que la devaluación del peso sea menor al diferencial de tasas durante el período de inversión.'
  },
  {
    icon: '📊',
    title: 'Banda Cambiaria',
    text: 'El análisis considera la banda cambiaria del BCRA que inició el 14/04/2025 con un crawling peg del 1% mensual. A partir del 01/01/2026, las bandas evolucionan según la inflación T-2 proyectada por el Relevamiento de Expectativas de Mercado (REM) del BCRA.'
  },
  {
    icon: '⚠️',
    title: 'Factores de Riesgo',
    text: 'Los principales riesgos incluyen: devaluación acelerada del peso, cambios en la política monetaria, riesgo de crédito soberano, y volatilidad de los mercados financieros locales.'
  }
]

export default function StrategyPanel({ mepRate }) {
  return (
    <section className="bg-white border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-navy-700 mb-4">¿Qué es el Carry Trade de Bonos?</h2>

      <p className="text-gray-700 mb-5 leading-relaxed">
        <strong>
          Esta estrategia consiste en vender USD al tipo de cambio MEP actual de $
          {mepRate ? mepRate.toFixed(0) : '—'}, comprar bonos en pesos, mantenerlos
          hasta el vencimiento y recomprar los dólares.
        </strong>
        {' '}El porcentaje que se presenta en la tabla es el rendimiento directo de esta
        estrategia completa medido en dólares.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {CARDS.map(({ icon, title, text }) => (
          <div key={title} className="bg-blue-50 border border-blue-100 p-4">
            <h4 className="font-semibold text-navy-700 mb-2">
              {icon} {title}
            </h4>
            <p className="text-sm text-gray-600 leading-relaxed">{text}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
