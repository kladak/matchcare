import { useMemo, useState } from 'react'
import { api, ApiError } from '../api'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import type { MatchResponse, UserMe } from '../types'

function pct(n: number) {
  return Math.round(n * 100)
}

function chipClass(n: number) {
  if (n >= 0.75) return 'chip good'
  if (n >= 0.4) return 'chip mid'
  return 'chip low'
}

export function MatchPage({ token, me, onToast }: { token: string; me: UserMe; onToast: (m: string) => void }) {
  const patient = me.patient
  const [specialties, setSpecialties] = useState((patient?.preferred_specialties ?? []).join(', '))
  const [city, setCity] = useState(patient?.city ?? '')
  const [region, setRegion] = useState(patient?.region ?? '')
  const [requireTier, setRequireTier] = useState(true)
  const [data, setData] = useState<MatchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [requesting, setRequesting] = useState<number | null>(null)

  const preferredList = useMemo(
    () =>
      specialties
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    [specialties],
  )

  async function runMatch() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.match(token, {
        preferred_specialties: preferredList,
        city: city || undefined,
        region: region || undefined,
        require_tier: requireTier,
        limit: 12,
      })
      setData(res)
      if (res.results.length) setExpanded(res.results[0].provider.user_id)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Match failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  async function requestMatch(providerUserId: number) {
    setRequesting(providerUserId)
    try {
      await api.createRequest(token, providerUserId, 'Requested from MatchCare demo UI')
      onToast('Match request sent')
    } catch (e) {
      onToast(e instanceof ApiError ? e.message : 'Could not create request')
    } finally {
      setRequesting(null)
    }
  }

  if (!patient) {
    return <EmptyState title="Patient profile required" detail="Sign in as a patient persona to run matches." />
  }

  return (
    <div>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Find matches</h2>
        <p className="muted">
          Explainable ranking for <strong>{me.display_name}</strong> · access tier{' '}
          <span className="badge">{patient.access_tier}</span> · org {me.organization.name}
        </p>
        <div className="grid-2">
          <div className="field">
            <label htmlFor="specs">Preferred specialties (comma-separated)</label>
            <input id="specs" value={specialties} onChange={(e) => setSpecialties(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="city">City</label>
            <input id="city" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="region">Region</label>
            <input id="region" value={region} onChange={(e) => setRegion(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="tier">Tier gate</label>
            <select
              id="tier"
              value={requireTier ? 'yes' : 'no'}
              onChange={(e) => setRequireTier(e.target.value === 'yes')}
            >
              <option value="yes">Require accepted tier</option>
              <option value="no">Show all (tier still scored)</option>
            </select>
          </div>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => void runMatch()} disabled={loading}>
          {loading ? 'Scoring…' : 'Run match'}
        </button>
      </section>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h3 style={{ marginTop: 0 }}>Ranked results</h3>
        {loading ? <LoadingState label="Computing specialty · location · tier · availability…" /> : null}
        {error ? <ErrorState message={error} onRetry={() => void runMatch()} /> : null}
        {!loading && !error && !data ? (
          <EmptyState title="No results yet" detail="Click Run match to score providers in your tenant." />
        ) : null}
        {!loading && data && data.results.length === 0 ? (
          <EmptyState title="No providers matched filters" detail="Try disabling the tier gate or widening specialties." />
        ) : null}
        {data?.formula ? <p className="muted">{data.formula}</p> : null}
        {data?.results.map((row) => {
          const open = expanded === row.provider.user_id
          return (
            <div className="match-row" key={row.provider.user_id}>
              <div className="score-ring" style={{ ['--pct' as string]: pct(row.score) }}>
                <span>{pct(row.score)}</span>
              </div>
              <div>
                <strong>{row.provider.display_name}</strong>
                <div className="muted">
                  {row.provider.city}, {row.provider.region} · {row.provider.remaining_slots}/
                  {row.provider.weekly_capacity} slots
                </div>
                <div className="chips">
                  {row.provider.specialties.map((s) => (
                    <span className="chip" key={s}>
                      {s}
                    </span>
                  ))}
                  <span className={chipClass(row.breakdown.specialty)}>spec {pct(row.breakdown.specialty)}%</span>
                  <span className={chipClass(row.breakdown.location)}>loc {pct(row.breakdown.location)}%</span>
                  <span className={chipClass(row.breakdown.tier)}>tier {pct(row.breakdown.tier)}%</span>
                  <span className={chipClass(row.breakdown.availability)}>
                    avail {pct(row.breakdown.availability)}%
                  </span>
                </div>
                {open ? (
                  <div className="breakdown">
                    {(['specialty', 'location', 'tier', 'availability'] as const).map((k) => (
                      <div key={k}>
                        <div className="bar-label">
                          <span>
                            {k} × {row.breakdown.weights[k]}
                          </span>
                          <span>{pct(row.breakdown[k])}%</span>
                        </div>
                        <div className="bar">
                          <i style={{ width: `${pct(row.breakdown[k])}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ marginTop: '0.5rem', paddingLeft: 0 }}
                  onClick={() => setExpanded(open ? null : row.provider.user_id)}
                >
                  {open ? 'Hide breakdown' : 'Show score breakdown'}
                </button>
              </div>
              <div className="actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={requesting === row.provider.user_id}
                  onClick={() => void requestMatch(row.provider.user_id)}
                >
                  {requesting === row.provider.user_id ? 'Sending…' : 'Request match'}
                </button>
              </div>
            </div>
          )
        })}
      </section>
    </div>
  )
}
