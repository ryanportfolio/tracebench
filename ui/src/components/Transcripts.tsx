import { useMemo, useState } from 'react'
import type { Transcript, TranscriptFilter } from '../lib/data'
import { filterTranscripts, uniqueSorted } from '../lib/data'

function Verdict({ passed }: { passed: boolean }) {
  return passed ? <span className="pass">✓ pass</span> : <span className="fail">✗ fail</span>
}

function TranscriptCard({ t }: { t: Transcript }) {
  return (
    <details className="transcript">
      <summary>
        <code>{t.task_id}</code> · {t.model_id} · run {t.run_index} · score {t.score.toFixed(2)}{' '}
        <Verdict passed={t.score >= 1} />
      </summary>
      <div className="body">
        <p className="meta">
          provider {t.provider}
          {t.provider_version ? ` · ${t.provider_version}` : ''} · seed {t.seed} ·{' '}
          {t.usage.input_tokens} in / {t.usage.output_tokens} out tokens · $
          {t.cost_usd.toFixed(4)}
        </p>
        {t.input_messages.map((m, i) => (
          <div key={i}>
            <p className="meta">{m.role}</p>
            <pre>{m.content}</pre>
          </div>
        ))}
        <p className="meta">output</p>
        <pre>{t.output_text}</pre>
        {t.tool_calls.length > 0 && (
          <div>
            <p className="meta">tool calls</p>
            <pre>{JSON.stringify(t.tool_calls, null, 2)}</pre>
          </div>
        )}
        <table>
          <thead>
            <tr>
              <th>check</th>
              <th>verdict</th>
              <th className="num">weight</th>
              <th>detail</th>
            </tr>
          </thead>
          <tbody>
            {t.checks.map((c, i) => (
              <tr key={i}>
                <td>
                  <code>{c.type}</code>
                </td>
                <td>
                  <Verdict passed={c.passed} />
                </td>
                <td className="num">{c.weight}</td>
                <td>{c.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

export function TranscriptExplorer({ transcripts }: { transcripts: Transcript[] }) {
  const [filter, setFilter] = useState<TranscriptFilter>({ verdict: 'all' })
  const models = useMemo(() => uniqueSorted(transcripts.map((t) => t.model_id)), [transcripts])
  const families = useMemo(() => uniqueSorted(transcripts.map((t) => t.family)), [transcripts])
  const visible = useMemo(() => filterTranscripts(transcripts, filter), [transcripts, filter])

  return (
    <div>
      <div className="filters">
        <select
          value={filter.model ?? ''}
          onChange={(e) => setFilter({ ...filter, model: e.target.value || undefined })}
          aria-label="filter by model"
        >
          <option value="">all models</option>
          {models.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
        <select
          value={filter.family ?? ''}
          onChange={(e) => setFilter({ ...filter, family: e.target.value || undefined })}
          aria-label="filter by family"
        >
          <option value="">all families</option>
          {families.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <select
          value={filter.verdict}
          onChange={(e) =>
            setFilter({ ...filter, verdict: e.target.value as TranscriptFilter['verdict'] })
          }
          aria-label="filter by verdict"
        >
          <option value="all">all verdicts</option>
          <option value="passed">score 1.00 only</option>
          <option value="failed">below 1.00 only</option>
        </select>
        <input
          type="search"
          placeholder="search task id or output text"
          value={filter.query ?? ''}
          onChange={(e) => setFilter({ ...filter, query: e.target.value })}
        />
      </div>
      <p className="meta">
        {visible.length} of {transcripts.length} transcripts
      </p>
      {visible.map((t) => (
        <TranscriptCard key={`${t.model_id}-${t.task_id}-${t.run_index}`} t={t} />
      ))}
    </div>
  )
}
