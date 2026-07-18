import { useMemo, useState } from 'react'
import type { FamilyAggregate, TaskAggregate } from '../lib/data'
import { ScoreBar } from './ScoreBar'

export function FamilyTable({ rows }: { rows: FamilyAggregate[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>model</th>
          <th>family</th>
          <th className="num">mean of task means</th>
          <th className="num">tasks</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {rows.map((f) => (
          <tr key={`${f.model_id}-${f.family}`}>
            <td>{f.model_id}</td>
            <td>
              <code>{f.family}</code>
            </td>
            <td className="num">{f.mean_of_task_means.toFixed(2)}</td>
            <td className="num">{f.n_tasks}</td>
            <td className="bar-cell">
              <ScoreBar score={f.mean_of_task_means} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

type SortKey = 'model_id' | 'task_id' | 'family' | 'mean_score' | 'stdev_score' | 'n'

export function TaskTable({ rows }: { rows: TaskAggregate[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id')
  const [descending, setDescending] = useState(false)

  const sorted = useMemo(() => {
    const copy = [...rows]
    copy.sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      const cmp = typeof av === 'number' ? av - (bv as number) : String(av).localeCompare(String(bv))
      return descending ? -cmp : cmp
    })
    return copy
  }, [rows, sortKey, descending])

  const header = (key: SortKey, label: string, numeric = false) => (
    <th
      className={`sortable${numeric ? ' num' : ''}`}
      onClick={() => {
        if (sortKey === key) setDescending(!descending)
        else {
          setSortKey(key)
          setDescending(false)
        }
      }}
    >
      {label}
      {sortKey === key ? (descending ? ' ▾' : ' ▴') : ''}
    </th>
  )

  return (
    <table>
      <thead>
        <tr>
          {header('model_id', 'model')}
          {header('task_id', 'task')}
          {header('family', 'family')}
          {header('mean_score', 'mean', true)}
          {header('stdev_score', 'stdev', true)}
          {header('n', 'n', true)}
          <th className="num">range</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {sorted.map((t) => (
          <tr key={`${t.model_id}-${t.task_id}`}>
            <td>{t.model_id}</td>
            <td>
              <code>{t.task_id}</code>
            </td>
            <td>{t.family}</td>
            <td className="num">{t.mean_score.toFixed(2)}</td>
            <td className="num">± {t.stdev_score.toFixed(2)}</td>
            <td className="num">{t.n}</td>
            <td className="num">
              {t.min_score.toFixed(2)}–{t.max_score.toFixed(2)}
            </td>
            <td className="bar-cell">
              <ScoreBar score={t.mean_score} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
