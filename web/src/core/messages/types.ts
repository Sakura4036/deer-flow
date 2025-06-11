// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

export type MessageRole = "user" | "assistant" | "tool";

export interface ProteinSequence {
  protein_name: string;
  accession?: string;
  organism_name?: string;
  sequence: string;
  gene_name?: string;
}

// export interface Interrupt {
//   interrupt_type: "plan_review" | "enzyme_selection";
//   content: string;
//   options: Option[];
//   extra_data: {
//     sequences?: ProteinSequence[];  // for enzyme_selection interrupt
//     [key: string]: any;
//   };
// }

export type Agent = "coordinator" | "planner" | "researcher" | "coder" | "reporter" | "enzyme_retriever" | "enzyme_designer" | "podcast";

export interface Message {
  id: string;
  threadId: string;
  agent?: Agent;
  role: MessageRole;
  isStreaming?: boolean;
  content: string;
  contentChunks: string[];
  toolCalls?: ToolCallRuntime[];
  finishReason?: "stop" | "interrupt" | "tool_calls";
  interruptFeedback?: string;
  resources?: Array<Resource>;
  interrupt_type?: "plan_review" | "enzyme_selection";
  options?: Option[];
  extra_data?: {
    sequences?: ProteinSequence[];  // for enzyme_selection interrupt
    [key: string]: any;
  };
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

export interface Resource {
  uri: string;
  title: string;
}