// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { AnimatePresence, motion } from "framer-motion";
import { ArrowUp, X } from "lucide-react";
import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { Detective } from "~/components/deer-flow/icons/detective";
import { Tooltip } from "~/components/deer-flow/tooltip";
import { Button } from "~/components/ui/button";
import type { Interrupt, Option } from "~/core/messages";
import {
  setEnableBackgroundInvestigation,
  useSettingsStore,
} from "~/core/store";
import { cn } from "~/lib/utils";

export function InputBox({
  className,
  size,
  responding,
  interrupt,
  onSend,
  onCancel,
  onClearInterrupt,
}: {
  className?: string;
  size?: "large" | "normal";
  responding?: boolean;
  interrupt?: Interrupt | null;
  onSend?: (message: string, options?: { interruptFeedback?: string }) => void;
  onCancel?: () => void;
  onClearInterrupt?: () => void;
}) {
  const [message, setMessage] = useState("");
  const [imeStatus, setImeStatus] = useState<"active" | "inactive">("inactive");
  const [indent, setIndent] = useState(0);
  const [selectedOption, setSelectedOption] = useState<Option | null>(null);
  const backgroundInvestigation = useSettingsStore(
    (state) => state.general.enableBackgroundInvestigation,
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedOption) {
      setMessage("");

      setTimeout(() => {
        if (feedbackRef.current) {
          setIndent(feedbackRef.current.offsetWidth);
        }
      }, 200);
    } else {
      setIndent(0);
    }
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  }, [selectedOption]);

  useEffect(() => {
    setSelectedOption(null);
  }, [interrupt]);

  const handleSendMessage = useCallback(() => {
    if (responding) {
      onCancel?.();
    } else {
      if (message.trim() === "" && !selectedOption) {
        return;
      }
      if (onSend) {
        onSend(message, {
          interruptFeedback: selectedOption?.value,
        });
        setMessage("");
        setSelectedOption(null);
        onClearInterrupt?.();
      }
    }
  }, [
    responding,
    onCancel,
    message,
    onSend,
    selectedOption,
    onClearInterrupt,
  ]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (responding) {
        return;
      }
      if (
        event.key === "Enter" &&
        !event.shiftKey &&
        !event.metaKey &&
        !event.ctrlKey &&
        imeStatus === "inactive"
      ) {
        event.preventDefault();
        handleSendMessage();
      }
    },
    [responding, imeStatus, handleSendMessage],
  );

  return (
    <div className={cn("bg-card relative rounded-[24px] border", className)}>
      {interrupt?.options && interrupt.options.length > 0 && !selectedOption && (
        <div className="flex flex-wrap items-center gap-2 border-b p-3">
          <p className="text-muted-foreground mr-2 text-sm">
            {interrupt.content}
          </p>
          {interrupt.options.map((option: Option) => (
            <Button
              key={option.value}
              variant="outline"
              size="sm"
              onClick={() => setSelectedOption(option)}
            >
              {option.text}
            </Button>
          ))}
        </div>
      )}
      <div className="w-full">
        <AnimatePresence>
          {selectedOption && (
            <motion.div
              ref={feedbackRef}
              className="bg-background border-brand absolute top-0 left-0 z-10 mt-3 ml-2 flex items-center justify-center gap-1 rounded-2xl border px-2 py-0.5"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
            >
              <div className="text-brand flex h-full w-full items-center justify-center text-sm opacity-90">
                {selectedOption.text}
              </div>
              <X
                className="cursor-pointer opacity-60"
                size={16}
                onClick={() => setSelectedOption(null)}
              />
            </motion.div>
          )}
        </AnimatePresence>
        <textarea
          ref={textareaRef}
          className={cn(
            "m-0 w-full resize-none border-none bg-transparent px-4 py-3 text-lg focus:outline-none",
            size === "large" ? "min-h-32" : "min-h-4",
          )}
          style={{ textIndent: selectedOption ? `${indent}px` : 0 }}
          placeholder={
            selectedOption
              ? `Provide details for '${selectedOption.text}'...`
              : interrupt
                ? "Select an option above or type your response"
                : "What can I do for you?"
          }
          value={message}
          onCompositionStart={() => setImeStatus("active")}
          onCompositionEnd={() => setImeStatus("inactive")}
          onKeyDown={handleKeyDown}
          onChange={(event) => {
            setMessage(event.target.value);
          }}
        />
      </div>
      <div className="flex items-center px-4 py-2">
        <div className="flex grow">
          <Tooltip
            className="max-w-60"
            title={
              <div>
                <h3 className="mb-2 font-bold">
                  Investigation Mode: {backgroundInvestigation ? "On" : "Off"}
                </h3>
                <p>
                  When enabled, DeerFlow will perform a quick search before
                  planning. This is useful for researches related to ongoing
                  events and news.
                </p>
              </div>
            }
          >
            <Button
              className={cn(
                "rounded-2xl",
                backgroundInvestigation && "!border-brand !text-brand",
              )}
              variant="outline"
              size="lg"
              onClick={() =>
                setEnableBackgroundInvestigation(!backgroundInvestigation)
              }
            >
              <Detective /> Investigation
            </Button>
          </Tooltip>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Tooltip title={responding ? "Stop" : "Send"}>
            <Button
              variant="outline"
              size="icon"
              className={cn("h-10 w-10 rounded-full")}
              onClick={handleSendMessage}
            >
              {responding ? (
                <div className="flex h-10 w-10 items-center justify-center">
                  <div className="bg-foreground h-4 w-4 rounded-sm opacity-70" />
                </div>
              ) : (
                <ArrowUp />
              )}
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
