import { useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import type { Provider } from '../types'

export function ProvidersPage({ token }: { token: string }) {
  const [rows, setRows] = useState<Provider[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [specialty, setSpecialty] = useState('')
  const [city, setCity] = useState('')

  async function load() {
    setError(null)
    setRows(null)
    try {
      setRows(
        await api.providers(token, {
          specialty: specialty || undefined,
          city: city || undefined,
        }),
      )
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load providers')
      setRows([])
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  return (
    <section className="card">
      <h2 style={{ marginTop: 0 }}>Browse providers</h2>
      <p className="muted">Tenant-scoped directory. Filters are optional.</p>
      <div className="grid-2">
        <div className="field">
          <label htmlFor="ps">Specialty</label>
          <input id="ps" value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Cardiology" />
        </div>
        <div className="field">
          <label htmlFor="pc">City</label>
          <input id="pc" value={city} onChange={(e) => setCity(e.target.value)} placeholder="San Francisco" />
        </div>
      </div>
      <button type="button" className="btn" onClick={() => void load()}>
        Apply filters
      </button>
      <div style={{ marginTop: '1rem' }}>
        {rows === null && !error ? <LoadingState /> : null}
        {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
        {rows && rows.length === 0 && !error ? <EmptyState title="No providers" detail="Try clearing filters." /> : null}
        {rows && rows.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialties</th>
                <th>Location</th>
                <th>Capacity</th>
                <th>Tiers</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.user_id}>
                  <td>
                    <strong>{p.display_name}</strong>
                    <div className="muted" style={{ fontSize: '0.8rem' }}>
                      {p.bio}
                    </div>
                  </td>
                  <td>{p.specialties.join(', ')}</td>
                  <td>
                    {p.city}, {p.region}
                  </td>
                  <td>
                    {p.remaining_slots}/{p.weekly_capacity}
                  </td>
                  <td>{p.accepted_tiers.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </section>
  )
}
