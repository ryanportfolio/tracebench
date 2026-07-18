/* Generated from ../schema/*.schema.json — do not edit. Run: npm run codegen */

export type Family = string;
export type MeanOfTaskMeans = number;
export type ModelId = string;
export type NTasks = number;
export type ByFamily = FamilyAggregate[];
export type Family1 = string;
export type MaxScore = number;
export type MeanScore = number;
export type MinScore = number;
export type ModelId1 = string;
export type N = number;
export type StdevScore = number;
export type TaskId = string;
export type ByTask = TaskAggregate[];
export type BaseSeed = number;
export type BudgetUsd = number;
export type MockScript = string | null;
/**
 * @minItems 1
 */
export type Models = [ModelConfig, ...ModelConfig[]];
export type ModelId2 = string;
export type InputPerMtok = number;
export type OutputPerMtok = number;
export type Provider = string;
export type Name = string;
export type RunsPerTask = number;
export type Tasks = string;
export type HaltedOnBudget = boolean;
export type NTranscripts = number;
export type TotalCostUsd = number;

export interface RunReport {
  by_family: ByFamily;
  by_task: ByTask;
  config: RunConfig;
  halted_on_budget: HaltedOnBudget;
  n_transcripts: NTranscripts;
  total_cost_usd: TotalCostUsd;
}
export interface FamilyAggregate {
  family: Family;
  mean_of_task_means: MeanOfTaskMeans;
  model_id: ModelId;
  n_tasks: NTasks;
}
export interface TaskAggregate {
  family: Family1;
  max_score: MaxScore;
  mean_score: MeanScore;
  min_score: MinScore;
  model_id: ModelId1;
  n: N;
  stdev_score: StdevScore;
  task_id: TaskId;
}
export interface RunConfig {
  base_seed?: BaseSeed;
  budget_usd: BudgetUsd;
  mock_script?: MockScript;
  models: Models;
  name: Name;
  runs_per_task?: RunsPerTask;
  tasks: Tasks;
}
export interface ModelConfig {
  model_id: ModelId2;
  params?: Params;
  pricing: Pricing;
  provider: Provider;
}
export interface Params {
  [k: string]: unknown;
}
/**
 * USD per million tokens. Pinned in config so cost math is auditable.
 */
export interface Pricing {
  input_per_mtok: InputPerMtok;
  output_per_mtok: OutputPerMtok;
}
