import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Auto-resize para embedding en iframe (igual que logos-carteras)
let lastHeight = 0
function broadcastHeight() {
  const height = document.documentElement.scrollHeight
  if (height !== lastHeight) {
    lastHeight = height
    window.parent.postMessage({ type: 'carry-resize', height }, '*')
  }
}
const ro = new ResizeObserver(broadcastHeight)
ro.observe(document.documentElement)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
