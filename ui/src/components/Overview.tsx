import { useEffect, useState } from 'react'
import type { FamilyAggregate, Manifest } from '../lib/data'
import { loadRunReport } from '../lib/data'
import { ScoreBar } from './ScoreBar'

interface Row {
  dir: string
  run: string
  nFailures: number
  fam: FamilyAggregate
}

/** Combined family leaderboard across every run in the manifest; the default
 * landing view so all families are visible without touching the run picker. */
export function Overview({
  manifest,
  onOpen,
}: {
  manifest: Manifest
  onOpen: (dir: string) => void
}) {
  const [rows, setRows] = useState<Row[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all(
      manifest.runs.map(async (r) => {
        const report = await loadRunReport(r.dir)
        return report.by_family.map((fam) => ({
          dir: r.dir,
          run: r.name,
          nFailures: r.n_failures,
          fam,
        }))
      }),
    )
      .then((groups) => {
        if (!cancelled) setRows(groups.flat().sort((a, b) => b.dir.localeCompare(a.dir)))
      })
      .catch((e) => {
        if (!cancelled) setError(String(e))
      })
    return () => {
      cancelled = true
    }
  }, [manifest])

  if (error) return <p className="error">{error}</p>
  if (!rows) return <p className="meta">loading…</p>
  return (
    <table>
      <thead>
        <tr>
          <th>model</th>
          <th>family</th>
          <th className="num">mean of task means</th>
          <th className="num">tasks</th>
          <th className="num">failures</th>
          <th>run</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={`${r.dir}-${r.fam.model_id}-${r.fam.family}`}>
            <td>{r.fam.model_id}</td>
            <td>
              <code>{r.fam.family}</code>
            </td>
            <td className="num">{r.fam.mean_of_task_means.toFixed(2)}</td>
            <td className="num">{r.fam.n_tasks}</td>
            <td className="num">{r.nFailures}</td>
            <td>
              <button onClick={() => onOpen(r.dir)}>{r.run}</button>
            </td>
            <td className="bar-cell">
              <ScoreBar score={r.fam.mean_of_task_means} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
