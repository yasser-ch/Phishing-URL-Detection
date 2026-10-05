import { useState } from "react"
import { useOutletContext } from "react-router-dom"

const CRITICAL_THRESHOLD = 85

function getTier(confidence) {
  return confidence >= CRITICAL_THRESHOLD ? "critical" : "moderate"
}

export default function Alerts() {
  const { alerts } = useOutletContext()
  const [filterStatus, setFilterStatus] = useState("all")
  const [minConfidence, setMinConfidence] = useState(0)
  const [search, setSearch] = useState("")

  const filtered = alerts.filter(a => {
    if (filterStatus !== "all" && a.status !== filterStatus) return false
    if (a.confidence < minConfidence) return false
    if (search && !a.url.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Alertes</div>
          <div className="page-subtitle">{alerts.length} alerte{alerts.length > 1 ? "s" : ""} au total</div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.2rem", paddingBottom: "1.2rem", borderBottom: "1px solid var(--border)", flexWrap: "wrap" }}>
          <input
            className="scanner-input"
            style={{ width: "240px" }}
            placeholder="Rechercher une URL..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            style={{ background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)", padding: "0.55rem 0.8rem", borderRadius: "6px", fontFamily: "var(--font-body)", fontSize: "0.8rem" }}
          >
            <option value="all">Tous statuts</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
          </select>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <label style={{ fontSize: "0.65rem", color: "var(--muted)" }}>Confiance min : {minConfidence}%</label>
            <input type="range" min="0" max="100" step="5" value={minConfidence} onChange={e => setMinConfidence(Number(e.target.value))} />
          </div>
          <span style={{ marginLeft: "auto", fontSize: "0.7rem", color: "var(--muted)" }}>
            {filtered.length} résultat{filtered.length > 1 ? "s" : ""}
          </span>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>URL</th>
              <th>Niveau</th>
              <th>Confiance</th>
              <th>Heure</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((alert, i) => {
              const tier = getTier(alert.confidence)
              const color = tier === "critical" ? "var(--critical)" : "var(--moderate)"
              return (
                <tr key={i} style={{ "--row-accent": color }} className="alert-enter">
                  <td className="mono" style={{ maxWidth: "380px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={alert.url}>
                    {alert.url}
                  </td>
                  <td><span className={`badge badge-${tier}`}>{tier === "critical" ? "Critique" : "Modéré"}</span></td>
                  <td className="mono" style={{ color }}>{alert.confidence}%</td>
                  <td className="muted-cell">{new Date(alert.timestamp).toLocaleTimeString()}</td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {filtered.length === 0 && <div className="empty">Aucune alerte ne correspond aux filtres.</div>}
      </div>
    </>
  )
}