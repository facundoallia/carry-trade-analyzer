import 'chart.js/auto'
import 'chartjs-adapter-date-fns'
import { Chart } from 'react-chartjs-2'

function getBreakevenColor(breakeven, bandCeiling) {
  const diff = (breakeven - bandCeiling) / bandCeiling
  if (diff > 0) return '#4caf50'      // Verde — breakeven por encima del techo
  if (diff > -0.11) return '#ffa726'  // Naranja — hasta -11% drawdown
  return '#ef5350'                     // Rojo — más de -11% drawdown
}

function buildChartData(chartData) {
  const bondPoints = chartData.expiration_dates.map((dateStr, i) => ({
    x: new Date(dateStr),
    y: chartData.mep_breakeven[i],
    ticker: chartData.tickers[i],
    bandCeiling: chartData.band_ceiling[i],
  }))

  const bandProjection = chartData.band_projection_dates.map((dateStr, i) => ({
    x: new Date(dateStr),
    y: chartData.band_projection_values[i],
  }))

  const pointColors = bondPoints.map(p => getBreakevenColor(p.y, p.bandCeiling))

  return {
    datasets: [
      {
        label: 'Techo de Banda Cambiaria',
        type: 'line',
        data: bandProjection,
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        order: 2,
      },
      {
        label: 'MEP Breakeven por Bono',
        type: 'scatter',
        data: bondPoints,
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 11,
        pointBackgroundColor: pointColors,
        pointBorderColor: '#1e3c72',
        pointBorderWidth: 2,
        showLine: false,
        order: 1,
      },
    ],
  }
}

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: { usePointStyle: true, padding: 16, font: { size: 12 } },
    },
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      titleColor: '#f8fafc',
      bodyColor: '#e2e8f0',
      padding: 12,
      callbacks: {
        title: (ctx) => {
          const dp = ctx[0].raw
          if (dp?.ticker) {
            return `${dp.ticker} — ${new Date(dp.x).toLocaleDateString('es-AR', {
              day: '2-digit', month: 'short', year: 'numeric'
            })}`
          }
          return new Date(ctx[0].parsed.x).toLocaleDateString('es-AR', {
            day: '2-digit', month: 'short', year: 'numeric'
          })
        },
        label: (ctx) => {
          const dp = ctx.raw
          if (dp?.ticker) {
            const diff = dp.y - dp.bandCeiling
            const pct = ((diff / dp.bandCeiling) * 100).toFixed(1)
            const icon = diff > 0 ? '🟢' : '🔴'
            return [
              `MEP Breakeven: $${dp.y.toFixed(0)}`,
              `Techo Banda:   $${dp.bandCeiling.toFixed(0)}`,
              `Diferencia:    $${diff.toFixed(0)} (${pct}%)`,
              `${icon} ${diff > 0 ? 'Por encima del techo' : 'Por debajo del techo'}`,
            ]
          }
          return `Techo Banda: $${ctx.parsed.y.toFixed(0)}`
        },
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'month',
        displayFormats: { month: 'MMM yyyy' },
        tooltipFormat: 'dd/MM/yyyy',
      },
      title: { display: true, text: 'Fecha de Vencimiento', font: { size: 12 } },
      ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } },
      grid: { color: 'rgba(0,0,0,0.06)' },
    },
    y: {
      title: { display: true, text: 'Valor en ARS', font: { size: 12 } },
      ticks: { callback: (v) => '$' + Number(v).toFixed(0) },
      grid: { color: 'rgba(0,0,0,0.06)' },
    },
  },
  interaction: { intersect: false, mode: 'nearest' },
}

export default function BreakevenChart({ chartData, loading }) {
  return (
    <section className="bg-white border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-navy-700 mb-4">
        Breakeven MEP vs Techo de Banda Cambiaria
      </h2>

      <div className="h-80 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-navy-700 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-gray-400">Generando visualización...</p>
            </div>
          </div>
        )}

        {!loading && chartData ? (
          <Chart
            type="scatter"
            data={buildChartData(chartData)}
            options={CHART_OPTIONS}
          />
        ) : !loading ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Sin datos de gráfico disponibles
          </div>
        ) : null}
      </div>

      <p className="mt-3 text-xs text-gray-400">
        🟢 Breakeven por encima del techo (carry positivo) &nbsp;|&nbsp;
        🟠 Hasta −11% debajo del techo &nbsp;|&nbsp;
        🔴 Más de −11% debajo del techo
      </p>
    </section>
  )
}
