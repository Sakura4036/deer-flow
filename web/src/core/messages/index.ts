// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

export * from "./types";
export * from "./merge-message";

export type MessageContent = string | ToolCall[];
export type MessageContentChunk = string | ToolCallChunk[];

export interface Option {
    text: string;
    value: string;
}

export interface Interrupt {
    id: string;
    role: "assistant";
    content: string;
    finish_reason: "interrupt";
    options: Option[];
}

export interface Message {
    id: string;
    role: "user" | "assistant" | "tool";
}
