import type { RunReport } from '../generated/run_report.schema'
import type { Transcript } from '../generated/transcript.schema'

export type { RunReport, Transcript }
export type TaskAggregate = RunReport['by_task'][number]
export type FamilyAggregate = RunReport['by_family'][number]

/** manifest.json is written by `tracebench ui-data`; shape kept in sync by hand
 * (it is UI plumbing, not a published artifact — the schema-checked contract
 * covers results.json and transcripts.jsonl). */
export interface ManifestRun {
  dir: string
  name: string
  n_transcripts: number
  total_cost_usd: number
  halted_on_budget: boolean
  models: string[]
  n_failures: number
}

export interface Manifest {
  runs: ManifestRun[]
  /** optional banner shown under the top bar */
  note?: string
}

export function parseJsonl<T>(text: string): T[] {
  return text
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as T)
}

export interface TranscriptFilter {
  model?: string
  family?: string
  verdict?: 'all' | 'passed' | 'failed'
  query?: string
}

export function filterTranscripts(
  transcripts: Transcript[],
  filter: TranscriptFilter,
): Transcript[] {
  const query = filter.query?.trim().toLowerCase() ?? ''
  return transcripts.filter((t) => {
    if (filter.model && t.model_id !== filter.model) return false
    if (filter.family && t.family !== filter.family) return false
    if (filter.verdict === 'passed' && t.score < 1) return false
    if (filter.verdict === 'failed' && t.score >= 1) return false
    if (query) {
      const haystack = `${t.task_id}\n${t.output_text}`.toLowerCase()
      if (!haystack.includes(query)) return false
    }
    return true
  })
}

export function uniqueSorted(values: string[]): string[] {
  return [...new Set(values)].sort()
}

async function fetchOk(url: string): Promise<Response> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`)
  return res
}

export async function loadManifest(baseUrl = 'data'): Promise<Manifest> {
  return (await fetchOk(`${baseUrl}/manifest.json`)).json()
}

export async function loadRunReport(dir: string, baseUrl = 'data'): Promise<RunReport> {
  return (await fetchOk(`${baseUrl}/${dir}/results.json`)).json()
}

export async function loadRun(
  dir: string,
  baseUrl = 'data',
): Promise<{ report: RunReport; transcripts: Transcript[] }> {
  const [report, jsonl] = await Promise.all([
    fetchOk(`${baseUrl}/${dir}/results.json`).then((r) => r.json()),
    fetchOk(`${baseUrl}/${dir}/transcripts.jsonl`).then((r) => r.text()),
  ])
  return { report, transcripts: parseJsonl<Transcript>(jsonl) }
}
