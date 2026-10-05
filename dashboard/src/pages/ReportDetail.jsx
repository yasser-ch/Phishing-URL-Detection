import { useEffect, useState } from "react"
import { useParams, useOutletContext, Link } from "react-router-dom"
import axios from "axios"

const CRITICAL_THRESHOLD = 85

function getTier(confidence) {
  return confidence >= CRITICAL_THRESHOLD ? "critical" : "moderate"
}

export default function ReportDetail() {
  const { reportId } = useParams()
  const { API } = useOutletContext()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    axios.get(`${API}/report/${reportId}`)
      .then(res => setReport(res.data))
      .catch(() => setError("Rapport introuvable."))
      .finally(() => setLoading(false))
  }, [reportId, API])

  if (loading) return <div className="empty">Chargement du rapport...</div>
  if (error) return <div className="empty">{error}</div>
  if (!report) return null

  const alerts = report.alerts || []

  return (
    <>
      <div className="topbar">
        <div>
          <Link to="/history" style={{ fontSize: "0.75rem", color: "var(--muted)", textDecoration: "none" }}>
            &larr; Retour à l'historique
          </Link>
          <div className="page-title mono" style={{ marginTop: "6px" }}>{report.report_id}</div>
          <div className="page-subtitle">{new Date(report.generated_at).toLocaleString()} · {report.source}</div>
        </div>
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="kpi-card neutral">
          <div className="kpi-label">Total analysées</div>
          <div className="kpi-value">{report.summary.total_analyzed}</div>
        </div>
        <div className="kpi-card critical">
          <div className="kpi-label">Malveillantes</div>
          <div className="kpi-value critical">{report.summary.malicious_detected}</div>
        </div>
        <div className="kpi-card safe">
          <div className="kpi-label">Bénignes</div>
          <div className="kpi-value safe">{report.summary.benign}</div>
        </div>
        <div className="kpi-card neutral">
          <div className="kpi-label">Taux détection</div>
          <div className="kpi-value">{report.summary.detection_rate}</div>
        </div>
      </div>

      <div className="card">
        <div className="section-title">Alertes de ce rapport ({alerts.length})</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>URL</th>
              <th>Niveau</th>
              <th>Confiance</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert, i) => {
              const tier = getTier(alert.confidence)
              const color = tier === "critical" ? "var(--critical)" : "var(--moderate)"
              return (
                <tr key={i} style={{ "--row-accent": color }}>
                  <td className="mono" style={{ maxWidth: "420px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={alert.url}>
                    {alert.url}
                  </td>
                  <td><span className={`badge badge-${tier}`}>{tier === "critical" ? "Critique" : "Modéré"}</span></td>
                  <td className="mono" style={{ color }}>{alert.confidence}%</td>
                  <td className="muted-cell">{alert.status}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {alerts.length === 0 && <div className="empty">Aucune alerte dans ce rapport.</div>}
      </div>
    </>
  )
}