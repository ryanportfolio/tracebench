import { useEffect, useState } from 'react'
import type { Manifest, RunReport, Transcript } from './lib/data'
import { loadManifest, loadRun } from './lib/data'
import { FamilyTable, TaskTable } from './components/Tables'
import { TranscriptExplorer } from './components/Transcripts'

type Theme = 'light' | 'dark'

function initialTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function SummaryTiles({ report }: { report: RunReport }) {
  const models = report.config.models.map((m) => `${m.provider}/${m.model_id}`).join(', ')
  return (
    <>
      <div className="tiles">
        <div className="tile">
          <div className="v">{report.config.name}</div>
          <div className="k">run</div>
        </div>
        <div className="tile">
          <div className="v">{report.n_transcripts}</div>
          <div className="k">transcripts</div>
        </div>
        <div className="tile">
          <div className="v">${report.total_cost_usd.toFixed(4)}</div>
          <div className="k">cost (cap ${report.config.budget_usd.toFixed(2)})</div>
        </div>
        <div className="tile">
          <div className="v">{report.config.runs_per_task}</div>
          <div className="k">runs per task</div>
        </div>
      </div>
      <p className="meta">models: {models}</p>
      {report.halted_on_budget && (
        <p className="banner">⚠ This run halted on its budget cap — results are partial.</p>
      )}
    </>
  )
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(initialTheme)
  const [manifest, setManifest] = useState<Manifest | null>(null)
  const [selected, setSelected] = useState<string>('')
  const [report, setReport] = useState<RunReport | null>(null)
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [error, setError] = useState<string>('')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    loadManifest()
      .then((m) => {
        setManifest(m)
        if (m.runs.length > 0) setSelected(m.runs[0].dir)
      })
      .catch((e) => setError(String(e)))
  }, [])

  useEffect(() => {
    if (!selected) return
    setError('')
    loadRun(selected)
      .then(({ report, transcripts }) => {
        setReport(report)
        setTranscripts(transcripts)
      })
      .catch((e) => setError(String(e)))
  }, [selected])

  return (
    <>
      <div className="topbar">
        <h1>tracebench</h1>
        {manifest && manifest.runs.length > 1 && (
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            aria-label="select run"
          >
            {manifest.runs.map((r) => (
              <option key={r.dir} value={r.dir}>
                {r.name} · {r.n_transcripts} transcripts · {r.n_failures} failures
              </option>
            ))}
          </select>
        )}
        <span className="spacer" />
        <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
          {theme === 'dark' ? '☀ light' : '☾ dark'}
        </button>
      </div>
      <p className="sub">
        Replayable agent evals distilled from real developer workflows — one practitioner's
        workflow-specific evals, not a general benchmark. Scores are mean over N runs with spread
        shown; no single-run claims.
      </p>
      {manifest?.note && <p className="banner">{manifest.note}</p>}
      {error && <p className="error">{error}</p>}
      {manifest && manifest.runs.length === 0 && (
        <p className="banner">No runs found. Produce one with `tracebench run`, then reload.</p>
      )}
      {report && (
        <>
          <SummaryTiles report={report} />
          <h2>Leaderboard by task family</h2>
          <FamilyTable rows={report.by_family} />
          <h2>Per-task scores</h2>
          <TaskTable rows={report.by_task} />
          <h2>Transcripts</h2>
          <TranscriptExplorer transcripts={transcripts} />
        </>
      )}
      <footer>
        Rendered from results.json + transcripts.jsonl ·{' '}
        <a href="https://github.com/ryanportfolio/tracebench">source</a>
      </footer>
    </>
  )
}
