export function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(1, score)) * 100
  return (
    <div className="bar" role="img" aria-label={`score ${score.toFixed(2)}`}>
      <i className={pct >= 99.95 ? 'full' : undefined} style={{ width: `${pct.toFixed(1)}%` }} />
    </div>
  )
}
