const API_BASE = import.meta.env.VITE_API_URL || ''

export async function fetchCarryData() {
  const res = await fetch(`${API_BASE}/api/carry-data`)
  if (!res.ok) throw new Error(`Error al cargar datos de carry (${res.status})`)
  return res.json()
}

export async function fetchChartData() {
  const res = await fetch(`${API_BASE}/api/chart-data`)
  if (!res.ok) throw new Error(`Error al cargar datos del gráfico (${res.status})`)
  return res.json()
}

export async function fetchRemData() {
  const res = await fetch(`${API_BASE}/api/rem-data`)
  if (!res.ok) throw new Error(`Error al cargar datos REM (${res.status})`)
  return res.json()
}
