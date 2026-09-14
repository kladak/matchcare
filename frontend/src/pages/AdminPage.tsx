import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import type { AuditLog, TenantSummary } from '../types'

export function AdminPage({ token }: { token: string }) {
  const [summary, setSummary] = useState<TenantSummary | null>(null)
  const [logs, setLogs] = useState<AuditLog[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const [t, a] = await Promise.all([api.tenant(token), api.auditLogs(token)])
      setSummary(t)
      setLogs(a)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load admin data')
    }
  }

  useEffect(() => {
    void load()
  }, [token])

  if (error) return <ErrorState message={error} onRetry={() => void load()} />
  if (!summary) return <LoadingState label="Loading tenant overview…" />

  return (
    <div>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Tenant overview</h2>
        <p className="muted">
          {summary.organization.name} · <code>{summary.organization.slug}</code> · subscription{' '}
          <span className="badge">{summary.organization.subscription_tier}</span>
        </p>
        <div className="grid-3">
          <div className="stat">
            <div className="value">{summary.patient_count}</div>
            <div className="label">Patients</div>
          </div>
          <div className="stat">
            <div className="value">{summary.provider_count}</div>
            <div className="label">Providers</div>
          </div>
          <div className="stat">
            <div className="value">{summary.open_requests}</div>
            <div className="label">Open requests</div>
          </div>
          <div className="stat">
            <div className="value">{summary.accepted_requests}</div>
            <div className="label">Accepted</div>
          </div>
          <div className="stat">
            <div className="value">{summary.scheduled_requests}</div>
            <div className="label">Scheduled</div>
          </div>
          <div className="stat">
            <div className="value">{summary.admin_count}</div>
            <div className="label">Admins</div>
          </div>
        </div>
        <h3>Specialties offered</h3>
        <div className="chips">
          {summary.specialties_offered.map((s) => (
            <span className="chip good" key={s}>
              {s}
            </span>
          ))}
        </div>
      </section>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h3 style={{ marginTop: 0 }}>Audit log</h3>
        <p className="muted">Metadata only — method, path, status, actor id. No request bodies or PHI.</p>
        {logs === null ? <LoadingState /> : null}
        {logs && logs.length === 0 ? <EmptyState title="No logs yet" detail="Hit a few authenticated routes." /> : null}
        {logs && logs.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Method</th>
                <th>Path</th>
                <th>Status</th>
                <th>Actor</th>
                <th>ms</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{l.id}</td>
                  <td>{l.method}</td>
                  <td>{l.path}</td>
                  <td>{l.status_code}</td>
                  <td>{l.actor_user_id ?? '—'}</td>
                  <td>{l.duration_ms}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>
    </div>
  )
}
