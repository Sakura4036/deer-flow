// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { nanoid } from "nanoid";
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { chatStream } from "~/core/api";
import { mergeMessage, type Interrupt, type Message } from "~/core/messages";
import { useSettingsStore } from "./settings-store";

const THREAD_ID = nanoid();

export interface Store {
  threadId: string;
  messages: Record<string, Message>;
  messageIds: string[];
  responding: boolean;
  interrupt: Interrupt | null;
  sendMessage: (
    message?: string,
    options?: { interruptFeedback?: string },
    streamOptions?: { abortSignal?: AbortSignal },
  ) => Promise<void>;
  appendMessage: (message: Message) => void;
  updateMessage: (message: Message) => void;
  clearConversation: () => void;
  clearInterrupt: () => void;
}

export const useStore = create<Store>()(
  devtools(
    persist(
      immer((set, get) => ({
        threadId: THREAD_ID,
        messages: {},
        messageIds: [],
        responding: false,
        interrupt: null,
        appendMessage: (message: Message) => {
          set((state) => {
            if (!state.messageIds.includes(message.id)) {
              state.messageIds.push(message.id);
            }
            state.messages[message.id] = message;
          });
        },
        updateMessage: (message: Message) => {
          set((state) => {
            state.messages[message.id] = message;
          });
        },
        clearInterrupt: () => {
          set({ interrupt: null });
        },
        sendMessage: async (
          message,
          options,
          streamOptions,
        ): Promise<void> => {
          if (get().responding) {
            return;
          }

          if (message) {
            get().appendMessage({
              id: nanoid(),
              role: "user",
              content: message,
              finishReason: "stop",
              threadId: get().threadId,
            });
          }

          const settings = useSettingsStore.getState();
          const previousMessages = Object.values(get().messages);
          set({ responding: true, interrupt: null });

          try {
            const stream = chatStream(
              {
                messages: previousMessages,
                thread_id: get().threadId,
                interrupt_feedback: options?.interruptFeedback,
                auto_accepted_plan: settings.general.autoAccept,
                max_plan_iterations: settings.agent.maxPlanIterations,
                max_step_num: settings.agent.maxStepNum,
                max_search_results: settings.agent.maxSearchResults,
                mcp_settings: settings.general.mcp,
                enable_background_investigation:
                  settings.general.enableBackgroundInvestigation,
              },
              {
                abortSignal: streamOptions?.abortSignal,
              },
            );
            for await (const chunk of stream) {
              if (chunk.event === "interrupt") {
                set({ interrupt: chunk.data as Interrupt, responding: false });
                continue;
              }
              const message = mergeMessage(
                get().messages[chunk.data.id],
                chunk,
              );
              get().updateMessage(message);
            }
          } catch (e) {
            if (e instanceof Error && e.name === "AbortError") {
              // do nothing
            } else {
              console.error(e);
            }
          } finally {
            set({ responding: false });
          }
        },
        clearConversation: () => {
          set({ messages: {}, messageIds: [] });
        },
      })),
      {
        name: "deer-flow-storage",
        partialize: (state) => ({
          threadId: state.threadId,
          messages: state.messages,
          messageIds: state.messageIds,
        }),
      },
    ),
    {
      name: "DeerFlow-Store",
    },
  ),
);

export const useMessageIds = () => useStore((state) => state.messageIds);
export const useMessage = (id: string) =>
  useStore((state) => state.messages[id]);
export const sendMessage = useStore.getState().sendMessage;
export const clearConversation = useStore.getState().clearConversation;