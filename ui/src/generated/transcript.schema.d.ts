/* Generated from ../schema/*.schema.json — do not edit. Run: npm run codegen */

export type Detail = string;
export type Passed = boolean;
export type Type = string;
export type Weight = number;
export type Checks = CheckResult[];
export type CostUsd = number;
export type TaskFamily = "discussions" | "tool_use" | "long_horizon" | "correction";
export type Content = string;
export type Role = "system" | "user" | "assistant" | "tool";
export type InputMessages = Message[];
export type ModelId = string;
export type OutputText = string;
export type Provider = string;
export type ProviderVersion = string;
export type RunIndex = number;
export type Score = number;
export type Seed = number;
export type TaskId = string;
export type Name = string;
export type ToolCalls = ToolCall[];
export type InputTokens = number;
export type OutputTokens = number;

/**
 * One graded run of one task against one model. The unit of publication.
 *
 * Designed to be reusable downstream as a training-data filter: it carries
 * the full input, the full output, per-check grades, and an overall score.
 */
export interface Transcript {
  checks: Checks;
  cost_usd: CostUsd;
  family: TaskFamily;
  input_messages: InputMessages;
  model_id: ModelId;
  output_text: OutputText;
  provider: Provider;
  provider_version?: ProviderVersion;
  run_index: RunIndex;
  score: Score;
  seed: Seed;
  task_id: TaskId;
  tool_calls: ToolCalls;
  usage: Usage;
}
export interface CheckResult {
  detail?: Detail;
  passed: Passed;
  type: Type;
  weight: Weight;
}
export interface Message {
  content: Content;
  role: Role;
}
export interface ToolCall {
  arguments?: Arguments;
  name: Name;
}
export interface Arguments {
  [k: string]: unknown;
}
export interface Usage {
  input_tokens?: InputTokens;
  output_tokens?: OutputTokens;
}
