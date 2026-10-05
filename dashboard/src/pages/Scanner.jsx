import { useState } from "react"
import { useOutletContext } from "react-router-dom"
import axios from "axios"

export default function Scanner() {
  const { API } = useOutletContext()
  const [analyzeUrl, setAnalyzeUrl] = useState("")
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeResult, setAnalyzeResult] = useState(null)

  const analyzeSingle = async () => {
    if (!analyzeUrl.trim()) return
    setAnalyzing(true)
    setAnalyzeResult(null)
    try {
      const res = await axios.post(`${API}/analyze`, { url: analyzeUrl })
      setAnalyzeResult(res.data)
    } catch (e) {
      setAnalyzeResult({ error: e.response?.data?.error || "Erreur d'analyse" })
    }
    setAnalyzing(false)
  }

  const verdictTier = analyzeResult && !analyzeResult.error
    ? (analyzeResult.verdict === "MALICIOUS"
      ? (analyzeResult.confidence >= 85 ? "critical" : "moderate")
      : "safe")
    : null

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Scanner</div>
          <div className="page-subtitle">Analyse d'une URL via blacklist, whitelist et modèle ML</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            className="scanner-input"
            placeholder="https://exemple-suspect.com/login"
            value={analyzeUrl}
            onChange={e => setAnalyzeUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && analyzeSingle()}
          />
          <button className="btn btn-primary" onClick={analyzeSingle} disabled={analyzing}>
            {analyzing ? "Analyse..." : "Analyser"}
          </button>
        </div>
      </div>

      {analyzeResult && !analyzeResult.error && (
        <div className="card verdict-enter">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border)" }}>
            <span className={`badge badge-${verdictTier}`}>
              {analyzeResult.verdict === "MALICIOUS" ? "Menace détectée" : "Aucune menace"}
            </span>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "1.8rem", fontWeight: 700 }}>
              {analyzeResult.confidence}%
            </span>
          </div>

          <div className="mono" style={{ fontSize: "0.85rem", marginBottom: "6px", wordBreak: "break-all" }}>
            {analyzeResult.url}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginBottom: "1.5rem" }}>
            {analyzeResult.detail}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", marginBottom: "1.5rem" }}>
            <div className="card">
              <div className="kpi-label">Méthode de détection</div>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, marginTop: "6px" }}>{analyzeResult.detection_method}</div>
            </div>
            <div className="card">
              <div className="kpi-label">Blacklist URLhaus</div>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, marginTop: "6px" }}>
                {analyzeResult.blacklist_hit ? "IOC connu" : "Non répertorié"}
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">Verdict ML</div>
              <div className="mono" style={{ fontSize: "0.85rem", fontWeight: 600, marginTop: "6px" }}>
                {analyzeResult.ml_verdict} · {analyzeResult.ml_confidence}%
              </div>
            </div>
          </div>

          <div className="section-title" style={{ fontSize: "0.8rem" }}>Features extraites</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "6px" }}>
            {Object.entries(analyzeResult.features).map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", background: "var(--background)", border: "1px solid var(--border)", borderRadius: "4px", padding: "0.45rem 0.7rem" }}>
                <span className="mono" style={{ fontSize: "0.65rem", color: "var(--muted)" }}>{k}</span>
                <span className="mono" style={{ fontSize: "0.72rem", color: "var(--foreground)", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {analyzeResult?.error && <div className="empty">{analyzeResult.error}</div>}

      {!analyzeResult && !analyzing && (
        <div className="empty">Entrez une URL pour l'analyser via blacklist URLhaus + modèle Machine Learning.</div>
      )}
    </>
  )
}