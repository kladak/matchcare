import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import type { MatchRequest, Role } from '../types'

export function RequestsPage({
  token,
  role,
  onToast,
}: {
  token: string
  role: Role
  onToast: (m: string) => void
}) {
  const [rows, setRows] = useState<MatchRequest[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  async function load() {
    setError(null)
    try {
      setRows(await api.listRequests(token))
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load requests')
      setRows([])
    }
  }

  useEffect(() => {
    void load()
  }, [token])

  async function patch(id: number, status: string) {
    setBusyId(id)
    try {
      await api.patchRequest(token, id, status)
      onToast(`Request ${status}`)
      await load()
    } catch (e) {
      onToast(e instanceof ApiError ? e.message : 'Update failed')
    } finally {
      setBusyId(null)
    }
  }

  const title = role === 'provider' ? 'Inbox' : role === 'admin' ? 'All requests' : 'My requests'

  return (
    <section className="card">
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p className="muted">Match requests are org-scoped. Providers accept / schedule; patients may decline.</p>
      {rows === null && !error ? <LoadingState /> : null}
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      {rows && rows.length === 0 && !error ? (
        <EmptyState title="No requests yet" detail="Patient path: Run match → Request match." />
      ) : null}
      {rows && rows.length > 0 ? (
        <table className="table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Provider</th>
              <th>Score</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.patient_name}</td>
                <td>{r.provider_name}</td>
                <td>{Math.round(r.score * 100)}</td>
                <td>
                  <span className="badge">{r.status}</span>
                  {r.appointment ? (
                    <div className="muted" style={{ fontSize: '0.75rem' }}>
                      appt {new Date(r.appointment.scheduled_for).toLocaleString()}
                    </div>
                  ) : null}
                </td>
                <td>
                  {role === 'provider' || role === 'admin' ? (
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="btn"
                        disabled={busyId === r.id || r.status === 'accepted'}
                        onClick={() => void patch(r.id, 'accepted')}
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={busyId === r.id}
                        onClick={() => void patch(r.id, 'scheduled')}
                      >
                        Propose appt
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger"
                        disabled={busyId === r.id}
                        onClick={() => void patch(r.id, 'declined')}
                      >
                        Decline
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={busyId === r.id || r.status === 'declined'}
                      onClick={() => void patch(r.id, 'declined')}
                    >
                      Decline
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  )
}
