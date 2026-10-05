import { useOutletContext } from "react-router-dom"
import { useCountUp } from "../hooks/useCountUp"

const CRITICAL_THRESHOLD = 85

function KpiCard({ label, value, tier, animate = true }) {
  const animated = useCountUp(animate ? (value ?? 0) : 0)
  return (
    <div className={`kpi-card ${tier}`}>
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${tier !== "neutral" ? tier : ""}`}>
        {animate ? animated : value}
      </div>
    </div>
  )
}

function BarRow({ label, value, total, color }) {
  const pct = total ? ((value ?? 0) / total * 100) : 0
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginBottom: "6px" }}>
        <span style={{ color: "var(--muted)" }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{value ?? 0}</span>
      </div>
      <div style={{ height: "6px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, transition: "width 400ms ease" }}></div>
      </div>
    </div>
  )
}

export default function Overview() {
  const { summary, alerts, scanning, runScan, report } = useOutletContext()

  const criticalCount = alerts.filter(a => a.confidence >= CRITICAL_THRESHOLD).length
  const moderateCount = alerts.length - criticalCount

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Vue d'ensemble</div>
          <div className="page-subtitle">{report?.report_id} · {report?.source}</div>
        </div>
        <button className="btn btn-primary" onClick={runScan} disabled={scanning}>
          {scanning ? "Scan en cours..." : "Lancer un scan"}
        </button>
      </div>

      <div className="kpi-grid">
        <KpiCard label="Total analysées" value={summary?.total_analyzed} tier="neutral" />
        <KpiCard label={`Critique (\u2265${CRITICAL_THRESHOLD}%)`} value={criticalCount} tier="critical" />
        <KpiCard label="Confiance modérée" value={moderateCount} tier="moderate" />
        <KpiCard label="Bénignes" value={summary?.benign} tier="safe" />
        <div className="kpi-card neutral">
          <div className="kpi-label">Taux détection</div>
          <div className="kpi-value">{summary?.detection_rate}</div>
        </div>
      </div>

      <div className="card">
        <div className="section-title">Répartition des menaces</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <BarRow label="Critique" value={criticalCount} total={summary?.total_analyzed} color="var(--critical)" />
          <BarRow label="Confiance modérée" value={moderateCount} total={summary?.total_analyzed} color="var(--moderate)" />
          <BarRow label="Bénignes" value={summary?.benign} total={summary?.total_analyzed} color="var(--safe)" />
        </div>
      </div>
    </>
  )
}