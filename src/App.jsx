import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import StrategyPanel from './components/StrategyPanel'
import CarryTable from './components/CarryTable'
import BreakevenChart from './components/BreakevenChart'
import SimulationPanel from './components/SimulationPanel'
import RemSection from './components/RemSection'
import ApiSection from './components/ApiSection'
import Footer from './components/Footer'
import { fetchCarryData, fetchChartData, fetchRemData } from './utils/api'

const AUTO_REFRESH_MS = 5 * 60 * 1000 // 5 minutos

export default function App() {
  const [carryData, setCarryData] = useState([])
  const [colorLimits, setColorLimits] = useState({})
  const [chartData, setChartData] = useState(null)
  const [remData, setRemData] = useState(null)
  const [mepRate, setMepRate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [carry, chart, rem] = await Promise.all([
        fetchCarryData(),
        fetchChartData(),
        fetchRemData()
      ])
      setCarryData(carry.data || [])
      setColorLimits(carry.color_limits || {})
      setMepRate(carry.mep_rate ?? null)
      setChartData(chart.chart_data || null)
      setRemData(rem.status === 'success' ? rem : null)
      setLastUpdate(new Date())
    } catch (err) {
      setError(err.message)
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, AUTO_REFRESH_MS)
    return () => clearInterval(interval)
  }, [loadData])

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Header
        mepRate={mepRate}
        lastUpdate={lastUpdate}
        onRefresh={loadData}
        loading={loading}
      />
      <div className="container mx-auto px-4 py-6 space-y-5 max-w-screen-2xl">
        <StrategyPanel mepRate={mepRate} />
        <CarryTable
          data={carryData}
          colorLimits={colorLimits}
          loading={loading}
          error={error}
        />
        <BreakevenChart chartData={chartData} loading={loading} />
        <SimulationPanel carryData={carryData} mepRate={mepRate} />
        <RemSection remData={remData} />
        <ApiSection />
      </div>
      <Footer />
    </div>
  )
}
