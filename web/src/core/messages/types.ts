// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

export type MessageRole = "user" | "assistant" | "tool";

export interface Message {
  id: string;
  threadId: string;
  agent?:
  | "coordinator"
  | "planner"
  | "researcher"
  | "coder"
  | "reporter"
  | "podcast"
  | "research_team"
  | "summary"
  | "patent_researcher"
  | "literature_researcher"
  | "coding_researcher"
  | "router";
  role: MessageRole;
  isStreaming?: boolean;
  content: string;
  contentChunks: string[];
  toolCalls?: ToolCallRuntime[];
  options?: Option[];
  finishReason?: "stop" | "interrupt" | "tool_calls";
  interruptFeedback?: string;
}

export interface Option {
  text: string;
  value: string;
}

export interface ToolCallRuntime {
  id: string;
  name: string;
  args: Record<string, unknown>;
  argsChunks?: string[];
  result?: string;
}

export const MessageActivatedAgents = [
  "researcher",
  "coder",
  "reporter",
  "research_team",
  "summary",
  "patent_researcher",
  "literature_researcher",
  "coding_researcher",
  "router",
]