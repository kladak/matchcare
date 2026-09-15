import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { DataNote } from '../components/DataNote'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import type { Persona } from '../types'

const PRIMARY_ORGS = new Set(['bayview'])

export function LoginPage({ onLogin }: { onLogin: (token: string) => Promise<void> }) {
  const [personas, setPersonas] = useState<Persona[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      setPersonas(await api.personas())
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load personas')
      setPersonas([])
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function continueAs(p: Persona) {
    setBusy(p.email)
    setError(null)
    try {
      const { access_token } = await api.login(p.email, p.password)
      await onLogin(access_token)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Login failed')
    } finally {
      setBusy(null)
    }
  }

  const primary = (personas ?? []).filter((p) => PRIMARY_ORGS.has(p.org_slug))
  const secondary = (personas ?? []).filter((p) => !PRIMARY_ORGS.has(p.org_slug))

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">MC</div>
          <div>
            <h1>MatchCare</h1>
            <p>Multi-tenant specialty matching</p>
          </div>
        </div>
      </header>
      <DataNote />
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Demo login</h2>
        <p className="muted">
          One-click JWT personas. Password for all: <code>demo1234</code>. Start with Bayview patient
          for the match walkthrough.
        </p>
        {error ? <ErrorState message={error} onRetry={load} /> : null}
        {personas === null ? <LoadingState label="Loading demo personas…" /> : null}
        {personas && personas.length === 0 && !error ? (
          <EmptyState title="No personas" detail="Is the API running on :8000?" />
        ) : null}
        {primary.length > 0 ? (
          <>
            <h3>Bayview Health Network</h3>
            <div className="persona-grid">
              {primary.map((p) => (
                <button
                  key={p.email}
                  type="button"
                  className="persona-card"
                  disabled={busy !== null}
                  onClick={() => void continueAs(p)}
                >
                  <span className={`badge role-${p.role}`}>{p.role}</span>
                  <h3>Continue as {p.display_name}</h3>
                  <p>{p.email}</p>
                  {busy === p.email ? <p className="muted">Signing in…</p> : null}
                </button>
              ))}
            </div>
          </>
        ) : null}
        {secondary.length > 0 ? (
          <>
            <h3 style={{ marginTop: '1.5rem' }}>Second tenant (isolation)</h3>
            <div className="persona-grid">
              {secondary.map((p) => (
                <button
                  key={p.email}
                  type="button"
                  className="persona-card"
                  disabled={busy !== null}
                  onClick={() => void continueAs(p)}
                >
                  <span className={`badge role-${p.role}`}>{p.role}</span>
                  <h3>{p.display_name}</h3>
                  <p>
                    {p.org_name} · {p.email}
                  </p>
                </button>
              ))}
            </div>
          </>
        ) : null}
      </section>
      <p className="footer-note">Seeded demo personas</p>
    </div>
  )
}
