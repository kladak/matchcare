export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return <div className="state-box loading" role="status">{label}</div>
}

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="state-box">
      <strong>{title}</strong>
      {detail ? <p className="muted">{detail}</p> : null}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-box error" role="alert">
      <strong>Something went wrong</strong>
      <p>{message}</p>
      {onRetry ? (
        <button type="button" className="btn" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  )
}
