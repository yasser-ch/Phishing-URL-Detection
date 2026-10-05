import { useOutletContext } from "react-router-dom"

export default function Settings() {
  const { schedulerStatus, intervalInput, setIntervalInput, schedulerSaving, toggleScheduler, updateInterval } = useOutletContext()

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Paramètres</div>
          <div className="page-subtitle">Configuration du scan automatique</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: "480px" }}>
        <div className="section-title">Scan automatique</div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "1.2rem" }}>
          <span style={{
            width: "8px", height: "8px", borderRadius: "50%",
            background: schedulerStatus?.enabled ? "var(--safe)" : "var(--muted)"
          }}></span>
          <span style={{ fontSize: "0.85rem" }}>
            {schedulerStatus?.enabled ? "Actif" : "Désactivé"}
          </span>
          {schedulerStatus?.enabled && schedulerStatus?.next_run && (
            <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
              · prochain scan : {new Date(schedulerStatus.next_run).toLocaleTimeString()}
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "1.2rem" }}>
          <label style={{ fontSize: "0.8rem", color: "var(--muted)" }}>Intervalle</label>
          <input
            type="number"
            min="1"
            value={intervalInput}
            onChange={e => setIntervalInput(Number(e.target.value))}
            style={{ width: "70px", background: "var(--background)", border: "1px solid var(--border)", color: "var(--foreground)", padding: "0.4rem 0.5rem", borderRadius: "6px", fontFamily: "var(--font-mono)", textAlign: "center" }}
          />
          <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>minutes</span>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn" onClick={updateInterval} disabled={schedulerSaving}>
            Appliquer l'intervalle
          </button>
          <button className="btn btn-primary" onClick={toggleScheduler} disabled={schedulerSaving}>
            {schedulerStatus?.enabled ? "Désactiver" : "Activer"}
          </button>
        </div>
      </div>
    </>
  )
}