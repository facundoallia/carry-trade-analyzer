import { RefreshCw } from 'lucide-react'

export default function Header({ mepRate, lastUpdate, onRefresh, loading }) {
  const timeStr = lastUpdate
    ? lastUpdate.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--:--:--'

  return (
    <header className="bg-gradient-to-r from-navy-800 to-navy-700 text-white shadow-lg">
      <div className="container mx-auto px-4 py-5 max-w-screen-2xl">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Analizador de Carry Trade — Bonos Argentinos
            </h1>
            <p className="text-blue-200 mt-1 text-sm">
              Análisis profesional de oportunidades de carry trade en bonos del Tesoro
            </p>
          </div>

          <div className="flex items-center gap-5">
            {mepRate && (
              <div className="text-right hidden sm:block">
                <p className="text-xs text-blue-200 uppercase tracking-wide">MEP actual</p>
                <p className="text-xl font-bold">${mepRate.toFixed(0)}</p>
              </div>
            )}
            <div className="text-right">
              <p className="text-xs text-blue-200">Última actualización</p>
              <p className="text-sm font-semibold tabular-nums">{timeStr}</p>
            </div>
            <button
              onClick={onRefresh}
              disabled={loading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500
                         disabled:opacity-50 disabled:cursor-not-allowed
                         text-white text-sm font-semibold px-4 py-2
                         transition-colors duration-150"
            >
              <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              Actualizar
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
