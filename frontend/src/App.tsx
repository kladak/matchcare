import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from './api'
import { Disclaimer } from './components/Disclaimer'
import { LoadingState } from './components/States'
import { AdminPage } from './pages/AdminPage'
import { LoginPage } from './pages/LoginPage'
import { MatchPage } from './pages/MatchPage'
import { ProvidersPage } from './pages/ProvidersPage'
import { RequestsPage } from './pages/RequestsPage'
import type { UserMe } from './types'

type Tab = 'match' | 'providers' | 'requests' | 'admin'

const TOKEN_KEY = 'matchcare_token'

export default function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [me, setMe] = useState<UserMe | null>(null)
  const [bootError, setBootError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('match')
  const [toast, setToast] = useState<string | null>(null)

  const showToast = useCallback((msg: string) => {
    setToast(msg)
    window.setTimeout(() => setToast(null), 2800)
  }, [])

  const hydrate = useCallback(async (t: string) => {
    setBootError(null)
    try {
      const user = await api.me(t)
      setMe(user)
      setToken(t)
      localStorage.setItem(TOKEN_KEY, t)
      if (user.role === 'patient') setTab('match')
      else if (user.role === 'provider') setTab('requests')
      else setTab('admin')
    } catch (e) {
      localStorage.removeItem(TOKEN_KEY)
      setToken(null)
      setMe(null)
      setBootError(e instanceof ApiError ? e.message : 'Session expired')
    }
  }, [])

  useEffect(() => {
    if (token && !me) void hydrate(token)
  }, [token, me, hydrate])

  function signOut() {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setMe(null)
    setTab('match')
  }

  if (!token || !me) {
    if (token && !bootError) {
      return (
        <div className="app-shell">
          <LoadingState label="Restoring session…" />
        </div>
      )
    }
    return (
      <LoginPage
        onLogin={async (t) => {
          await hydrate(t)
        }}
      />
    )
  }

  const tabs: { id: Tab; label: string; show: boolean }[] = [
    { id: 'match', label: 'Find matches', show: me.role === 'patient' },
    { id: 'providers', label: 'Providers', show: true },
    {
      id: 'requests',
      label: me.role === 'provider' ? 'Inbox' : 'Requests',
      show: true,
    },
    { id: 'admin', label: 'Tenant', show: me.role === 'admin' },
  ]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">MC</div>
          <div>
            <h1>MatchCare</h1>
            <p>
              {me.organization.name} · {me.organization.subscription_tier} tier
            </p>
          </div>
        </div>
        <div className="user-chip">
          <div>
            <strong>{me.display_name}</strong>
            <div>
              <span className={`badge role-${me.role}`}>{me.role}</span>{' '}
              <span>{me.email}</span>
            </div>
          </div>
          <button type="button" className="btn btn-ghost" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <Disclaimer />

      <nav className="nav" aria-label="Primary">
        {tabs
          .filter((t) => t.show)
          .map((t) => (
            <button
              key={t.id}
              type="button"
              className={tab === t.id ? 'active' : ''}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
      </nav>

      {tab === 'match' && me.role === 'patient' ? (
        <MatchPage token={token} me={me} onToast={showToast} />
      ) : null}
      {tab === 'providers' ? <ProvidersPage token={token} /> : null}
      {tab === 'requests' ? (
        <RequestsPage token={token} role={me.role} onToast={showToast} />
      ) : null}
      {tab === 'admin' && me.role === 'admin' ? <AdminPage token={token} /> : null}

      {toast ? <div className="toast">{toast}</div> : null}
      <p className="footer-note">
        Synthetic educational demo · formula in SPEC.md · not a medical device
      </p>
    </div>
  )
}
