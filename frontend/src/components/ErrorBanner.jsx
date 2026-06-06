export default function ErrorBanner({ message, clarify, clarifyMessage }) {
  if (!message && !clarify) return null

  if (clarify) {
    return (
      <div className="w-full rounded-xl border border-accent/30 bg-accent/5 px-5 py-4 text-sm text-ink animate-fade-in">
        <p className="font-semibold text-accent mb-1">Clarification needed</p>
        <p className="text-ink-2">{clarifyMessage}</p>
      </div>
    )
  }

  return (
    <div className="w-full rounded-xl border border-danger/30 bg-danger/5 px-5 py-4 text-sm animate-fade-in">
      <p className="font-semibold text-danger mb-1">Error</p>
      <p className="text-ink-2">{message}</p>
    </div>
  )
}
