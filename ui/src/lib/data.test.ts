import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { Ajv } from 'ajv'
import type { RunReport, Transcript } from './data'
import { filterTranscripts, parseJsonl, uniqueSorted } from './data'

const fixtures = join(__dirname, '..', 'test-fixtures')
const schemas = join(__dirname, '..', '..', 'schema')

const results = JSON.parse(readFileSync(join(fixtures, 'results.json'), 'utf-8')) as RunReport
const transcripts = parseJsonl<Transcript>(
  readFileSync(join(fixtures, 'transcripts.jsonl'), 'utf-8'),
)

describe('contract: harness artifacts validate against the committed schemas', () => {
  // The fixtures are real harness output (the mock dry run). If the pydantic
  // models change shape, `tracebench schema` regenerates the schemas, codegen
  // regenerates the TS types, and this test catches stale fixtures.
  const ajv = new Ajv({ strict: false })

  it('results.json matches run_report.schema.json', () => {
    const schema = JSON.parse(readFileSync(join(schemas, 'run_report.schema.json'), 'utf-8'))
    const valid = ajv.validate(schema, results)
    expect(ajv.errors ?? []).toEqual([])
    expect(valid).toBe(true)
  })

  it('every transcript line matches transcript.schema.json', () => {
    const schema = JSON.parse(readFileSync(join(schemas, 'transcript.schema.json'), 'utf-8'))
    expect(transcripts.length).toBeGreaterThan(0)
    for (const t of transcripts) {
      const valid = ajv.validate(schema, t)
      expect(ajv.errors ?? []).toEqual([])
      expect(valid).toBe(true)
    }
  })
})

describe('parseJsonl', () => {
  it('parses one object per non-empty line', () => {
    expect(parseJsonl<{ a: number }>('{"a":1}\n{"a":2}\n\n')).toEqual([{ a: 1 }, { a: 2 }])
  })

  it('throws on malformed lines instead of skipping silently', () => {
    expect(() => parseJsonl('{"a":1}\nnot json')).toThrow()
  })
})

describe('filterTranscripts', () => {
  it('no filter returns everything', () => {
    expect(filterTranscripts(transcripts, {})).toHaveLength(transcripts.length)
  })

  it('filters by model', () => {
    const out = filterTranscripts(transcripts, { model: 'mock-baseline' })
    expect(out.length).toBeGreaterThan(0)
    expect(filterTranscripts(transcripts, { model: 'nope' })).toHaveLength(0)
  })

  it('filters by verdict', () => {
    const passed = filterTranscripts(transcripts, { verdict: 'passed' })
    const failed = filterTranscripts(transcripts, { verdict: 'failed' })
    expect(passed.length + failed.length).toBe(transcripts.length)
  })

  it('searches task id and output text case-insensitively', () => {
    const byId = filterTranscripts(transcripts, { query: 'DISC-000' })
    expect(byId.length).toBeGreaterThan(0)
    expect(filterTranscripts(transcripts, { query: 'zz-no-match-zz' })).toHaveLength(0)
  })
})

describe('uniqueSorted', () => {
  it('dedupes and sorts', () => {
    expect(uniqueSorted(['b', 'a', 'b'])).toEqual(['a', 'b'])
  })
})
