import { useOutletContext, Link } from "react-router-dom"

export default function History() {
  const { history } = useOutletContext()

  return (
    <>
      <div className="topbar">
        <div>
          <div className="page-title">Historique</div>
          <div className="page-subtitle">{history.length} rapport{history.length > 1 ? "s" : ""} archivé{history.length > 1 ? "s" : ""}</div>
        </div>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Report ID</th>
              <th>Date</th>
              <th>Analysées</th>
              <th>Malveillantes</th>
              <th>Taux</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h, i) => (
              <tr key={i}>
                <td className="mono">
                  <Link to={`/history/${h.report_id}`} style={{ color: "var(--primary)", textDecoration: "none" }}>
                    {h.report_id}
                  </Link>
                </td>
                <td className="muted-cell">{new Date(h.generated_at).toLocaleString()}</td>
                <td>{h.summary.total_analyzed}</td>
                <td style={{ color: "var(--critical)" }}>{h.summary.malicious_detected}</td>
                <td>{h.summary.detection_rate}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {history.length === 0 && <div className="empty">Aucun rapport dans l'historique.</div>}
      </div>
    </>
  )
}