import { useState, useEffect } from "react"
import { Routes, Route, Outlet } from "react-router-dom"
import axios from "axios"
import Sidebar from "./components/Sidebar"
import Overview from "./pages/Overview"
import Scanner from "./pages/Scanner"
import Alerts from "./pages/Alerts"
import History from "./pages/History"
import ReportDetail from "./pages/ReportDetail"
import Settings from "./pages/Settings"

const API = "http://localhost:5000/api"

function Layout(props) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Outlet context={props} />
      </div>
    </div>
  )
}

export default function App() {
  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [report, setReport] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [intervalInput, setIntervalInput] = useState(60)
  const [schedulerSaving, setSchedulerSaving] = useState(false)

  const loadData = async () => {
    try {
      const [s, a, r, h] = await Promise.all([
        axios.get(`${API}/summary`),
        axios.get(`${API}/alerts`),
        axios.get(`${API}/report`),
        axios.get(`${API}/history`)
      ])
      setSummary(s.data)
      setAlerts(a.data)
      setReport(r.data)
      setHistory(h.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const loadSchedulerStatus = async () => {
    try {
      const res = await axios.get(`${API}/scheduler/status`)
      setSchedulerStatus(res.data)
      if (res.data.interval_minutes) setIntervalInput(res.data.interval_minutes)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadData()
    loadSchedulerStatus()
  }, [])

  const runScan = async () => {
    setScanning(true)
    try {
      await axios.post(`${API}/scan`, { limit: 100 })
      await loadData()
    } catch (e) {
      console.error(e)
    }
    setScanning(false)
  }

  const toggleScheduler = async () => {
    setSchedulerSaving(true)
    try {
      const res = await axios.post(`${API}/scheduler/config`, {
        enabled: !schedulerStatus?.enabled,
        interval_minutes: intervalInput
      })
      setSchedulerStatus(res.data)
    } catch (e) {
      console.error(e)
    }
    setSchedulerSaving(false)
  }

  const updateInterval = async () => {
    setSchedulerSaving(true)
    try {
      const res = await axios.post(`${API}/scheduler/config`, {
        enabled: true,
        interval_minutes: intervalInput
      })
      setSchedulerStatus(res.data)
    } catch (e) {
      console.error(e)
    }
    setSchedulerSaving(false)
  }

  if (loading) return <div className="loading">CHARGEMENT...</div>

  const sharedContext = {
    summary, alerts, report, history,
    scanning, runScan,
    schedulerStatus, intervalInput, setIntervalInput, schedulerSaving,
    toggleScheduler, updateInterval,
    API,
  }

  return (
    <Routes>
      <Route element={<Layout {...sharedContext} />}>
        <Route index element={<Overview />} />
        <Route path="scanner" element={<Scanner />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="history" element={<History />} />
        <Route path="history/:reportId" element={<ReportDetail />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}