// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { LoadingOutlined } from "@ant-design/icons";
import { motion } from "framer-motion";
import { Download, Headphones } from "lucide-react";
import { useCallback, useMemo, useRef, useState } from "react";
import { useShallow } from "zustand/react/shallow";

import { LoadingAnimation } from "~/components/deer-flow/loading-animation";
import { Markdown } from "~/components/deer-flow/markdown";
import { RainbowText } from "~/components/deer-flow/rainbow-text";
import { RollingText } from "~/components/deer-flow/rolling-text";
import {
  ScrollContainer,
  type ScrollContainerRef,
} from "~/components/deer-flow/scroll-container";
import { Tooltip } from "~/components/deer-flow/tooltip";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Checkbox } from "~/components/ui/checkbox";
import { Label } from "~/components/ui/label";
import type { Message, Option } from "~/core/messages";
import {
  closeResearch,
  openResearch,
  useLastFeedbackMessageId,
  useLastInterruptMessage,
  useMessage,
  useMessageIds,
  useResearchMessage,
  useStore,
  listenToPodcast,
} from "~/core/store";
import { parseJSON } from "~/core/utils";
import { cn } from "~/lib/utils";

export interface ProteinSequence {
  name: string;
  sequence: string;
  id?: string;
  source?: string;
  description?: string;
}

export function MessageListView({
  className,
  onFeedback,
  onSendMessage,
}: {
  className?: string;
  onFeedback?: (feedback: { option: Option }) => void;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
}) {
  const scrollContainerRef = useRef<ScrollContainerRef>(null);
  const messageIds = useMessageIds();
  const interruptMessage = useLastInterruptMessage();
  const waitingForFeedbackMessageId = useLastFeedbackMessageId();
  const responding = useStore((state) => state.responding);
  const noOngoingResearch = useStore(
    (state) => state.ongoingResearchId === null,
  );
  const ongoingResearchIsOpen = useStore(
    (state) => state.ongoingResearchId === state.openResearchId,
  );

  const handleToggleResearch = useCallback(() => {
    // Fix the issue where auto-scrolling to the bottom
    // occasionally fails when toggling research.
    const timer = setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollToBottom();
      }
    }, 500);
    return () => {
      clearTimeout(timer);
    };
  }, []);

  return (
    <ScrollContainer
      className={cn("flex h-full w-full flex-col overflow-hidden", className)}
      scrollShadowColor="var(--app-background)"
      autoScrollToBottom
      ref={scrollContainerRef}
    >
      <ul className="flex flex-col">
        {messageIds.map((messageId) => (
          <MessageListItem
            key={messageId}
            messageId={messageId}
            waitForFeedback={waitingForFeedbackMessageId === messageId}
            interruptMessage={interruptMessage}
            onFeedback={onFeedback}
            onSendMessage={onSendMessage}
            onToggleResearch={handleToggleResearch}
          />
        ))}
        <div className="flex h-8 w-full shrink-0"></div>
      </ul>
      {responding && (noOngoingResearch || !ongoingResearchIsOpen) && (
        <LoadingAnimation className="ml-4" />
      )}
    </ScrollContainer>
  );
}

function MessageListItem({
  className,
  messageId,
  waitForFeedback,
  interruptMessage,
  onFeedback,
  onSendMessage,
  onToggleResearch,
}: {
  className?: string;
  messageId: string;
  waitForFeedback?: boolean;
  onFeedback?: (feedback: { option: Option }) => void;
  interruptMessage?: Message | null;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
  onToggleResearch?: () => void;
}) {
  const message = useMessage(messageId);
  const researchIds = useStore((state) => state.researchIds);
  const startOfResearch = useMemo(() => {
    return researchIds.includes(messageId);
  }, [researchIds, messageId]);
  if (message) {
    if (
      message.role === "user" ||
      message.agent === "coordinator" ||
      message.agent === "planner" ||
      message.agent === "podcast" ||
      startOfResearch ||
      interruptMessage?.id === messageId
    ) {
      let content: React.ReactNode;
      if (message.agent === "planner") {
        content = (
          <div className="w-full px-4">
            <PlanCard
              message={message}
              waitForFeedback={waitForFeedback}
              interruptMessage={interruptMessage}
              onFeedback={onFeedback}
              onSendMessage={onSendMessage}
            />
          </div>
        );
      } else if (message.agent === "podcast") {
        content = (
          <div className="w-full px-4">
            <PodcastCard message={message} />
          </div>
        );
      } else if (startOfResearch) {
        content = (
          <div className="w-full px-4">
            <ResearchCard
              researchId={message.id}
              onToggleResearch={onToggleResearch}
            />
          </div>
        );
      } else if (
        interruptMessage?.id === messageId &&
        (interruptMessage?.interrupt as any)?.type === "enzyme_selection"
      ) {
        content = (
          <div className="w-full px-4">
            <EnzymeSelectionCard
              message={interruptMessage}
              waitForFeedback={waitForFeedback}
              interruptMessage={interruptMessage}
              onFeedback={onFeedback}
              onSendMessage={onSendMessage}
            />
          </div>
        );
      } else {
        content = message.content ? (
          <div
            className={cn(
              "flex w-full px-4",
              message.role === "user" && "justify-end",
              className,
            )}
          >
            <MessageBubble message={message}>
              <div className="flex w-full flex-col text-wrap break-words">
                <Markdown animated isStreaming={message.isStreaming}>
                  {message?.content}
                </Markdown>
              </div>
            </MessageBubble>
          </div>
        ) : null;
      }
      if (content) {
        return (
          <motion.li
            className="mt-10"
            key={messageId}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ transition: "all 0.2s ease-out" }}
            transition={{
              duration: 0.2,
              ease: "easeOut",
            }}
          >
            {content}
          </motion.li>
        );
      }
    }
    return null;
  }
}

function MessageBubble({
  className,
  message,
  children,
}: {
  className?: string;
  message: Message;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        `flex w-fit max-w-[85%] flex-col rounded-2xl px-4 py-3 shadow`,
        message.role === "user" &&
        "text-primary-foreground bg-brand rounded-ee-none",
        message.role === "assistant" && "bg-card rounded-es-none",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ResearchCard({
  className,
  researchId,
  onToggleResearch,
}: {
  className?: string;
  researchId: string;
  onToggleResearch?: () => void;
}) {
  const researchMessage = useResearchMessage(researchId);
  const researchStarterMessage = useMessage(researchId);
  const { messages, openResearch, closeResearch } = useStore(
    useShallow((state) => ({
      messages: state.researchActivityIds.get(researchId),
      openResearch: state.openResearch,
      closeResearch: state.closeResearch,
    })),
  );
  const isOpen = useStore((state) => state.openResearchId === researchId);
  const ongoingResearchId = useStore((state) => state.ongoingResearchId);
  const isOngoing = ongoingResearchId === researchId;

  const [isGenerating, setIsGenerating] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const handleListen = useCallback(async (researchId: string) => {
    setIsGenerating(true);
    try {
      await listenToPodcast(researchId);
      setIsListening(true);
    } catch (error) {
      console.error("Failed to generate or play podcast", error);
      // Optionally, show a toast notification to the user
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const handleToggle = useCallback(() => {
    if (isOpen) {
      closeResearch();
    } else {
      openResearch(researchId);
    }
    onToggleResearch?.();
  }, [isOpen, researchId, onToggleResearch, openResearch, closeResearch]);
  if (!researchMessage) {
    return null;
  }
  const status = useMemo(() => {
    if (isOngoing) {
      return "Researching...";
    }
    if (researchMessage?.agent === "reporter") {
      return "Report generated";
    }
    return "";
  }, [isOngoing, researchMessage]);

  const title = useMemo(() => {
    if (researchStarterMessage?.agent === "enzyme_retriever") {
      return "酶挖掘任务";
    }
    return researchMessage?.plan?.title;
  }, [researchStarterMessage, researchMessage]);

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle>
          <RainbowText animated={status !== "Report generated"}>
            {title ?? "Deep Research"}
          </RainbowText>
        </CardTitle>
      </CardHeader>
      <CardFooter>
        <div className="flex w-full">
          <RollingText className="text-muted-foreground flex-grow text-sm">
            {status}
          </RollingText>
          <Button
            variant={!isOpen ? "default" : "outline"}
            onClick={handleToggle}
          >
            {isOpen ? "Close" : "Open"}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

const GREETINGS = ["Cool", "Sounds great", "Looks good", "Great", "Awesome"];
function PlanCard({
  className,
  message,
  interruptMessage,
  onFeedback,
  waitForFeedback,
  onSendMessage,
}: {
  className?: string;
  message: Message;
  interruptMessage?: Message | null;
  onFeedback?: (feedback: { option: Option }) => void;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
  waitForFeedback?: boolean;
}) {
  const plan = useMemo<{
    title?: string;
    thought?: string;
    steps?: { title?: string; description?: string }[];
  }>(() => {
    return parseJSON(message.content ?? "", {});
  }, [message.content]);
  const handleAccept = useCallback(async () => {
    if (onSendMessage) {
      onSendMessage(
        `${GREETINGS[Math.floor(Math.random() * GREETINGS.length)]}! ${Math.random() > 0.5 ? "Let's get started." : "Let's start."}`,
        {
          interruptFeedback: "accepted",
        },
      );
    }
  }, [onSendMessage]);
  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle>
          <Markdown animated>
            {`### ${plan.title !== undefined && plan.title !== ""
              ? plan.title
              : "Deep Research"
              }`}
          </Markdown>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Markdown className="opacity-80" animated>
          {plan.thought}
        </Markdown>
        {plan.steps && (
          <ul className="my-2 flex list-decimal flex-col gap-4 border-l-[2px] pl-8">
            {plan.steps.map((step, i) => (
              <li key={`step-${i}`}>
                <h3 className="mb text-lg font-medium">
                  <Markdown animated>{step.title}</Markdown>
                </h3>
                <div className="text-muted-foreground text-sm">
                  <Markdown animated>{step.description}</Markdown>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
      <CardFooter className="flex justify-end">
        {!message.isStreaming && interruptMessage?.options?.length && (
          <motion.div
            className="flex gap-2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            {interruptMessage?.options.map((option) => (
              <Button
                key={option.value}
                variant={option.value === "accepted" ? "default" : "outline"}
                disabled={!waitForFeedback}
                onClick={() => {
                  if (option.value === "accepted") {
                    void handleAccept();
                  } else {
                    onFeedback?.({
                      option,
                    });
                  }
                }}
              >
                {option.text}
              </Button>
            ))}
          </motion.div>
        )}
      </CardFooter>
    </Card>
  );
}

function EnzymeSelectionCard({
  className,
  message,
  interruptMessage,
  onFeedback,
  onSendMessage,
  waitForFeedback,
}: {
  className?: string;
  message: Message;
  interruptMessage?: Message | null;
  onFeedback?: (feedback: { option: Option }) => void;
  onSendMessage?: (
    message: string,
    options?: { interruptFeedback?: string },
  ) => void;
  waitForFeedback?: boolean;
}) {
  const [selectedSequences, setSelectedSequences] = useState<string[]>([]);

  const handleSequenceSelection = (sequenceId: string) => {
    setSelectedSequences((prev) =>
      prev.includes(sequenceId)
        ? prev.filter((id) => id !== sequenceId)
        : [...prev, sequenceId],
    );
  };

  const handleAccept = useCallback(async () => {
    if (onSendMessage) {
      const selected = (interruptMessage as any)?.sequences?.filter(
        (s: ProteinSequence) => s.id && selectedSequences.includes(s.id),
      );
      const sequenceNames = selected?.map((s: ProteinSequence) => s.name).join(", ");
      onSendMessage(
        `Please proceed with designing mutants for the following sequences: ${sequenceNames}. Selected IDs: ${selectedSequences.join(
          ", ",
        )}`,
        {
          interruptFeedback: "accept_sequences",
        },
      );
    }
  }, [onSendMessage, selectedSequences, interruptMessage]);

  const sequences: ProteinSequence[] =
    (interruptMessage as any)?.sequences ?? [];

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle>Enzyme Selection</CardTitle>
      </CardHeader>
      <CardContent>
        <Markdown className="opacity-80" animated>
          {interruptMessage?.content}
        </Markdown>
        {sequences.length > 0 && (
          <div className="my-4 space-y-4">
            <h3 className="text-lg font-medium">Available Sequences:</h3>
            <div className="max-h-60 overflow-y-auto rounded-md border p-2">
              <ul className="space-y-3 p-2">
                {sequences.map((seq: ProteinSequence) => (
                  <li
                    key={seq.id}
                    className="flex items-start space-x-3 rounded-md border p-4"
                  >
                    <Checkbox
                      id={seq.id}
                      checked={selectedSequences.includes(seq.id!)}
                      onCheckedChange={() => handleSequenceSelection(seq.id!)}
                    />
                    <div className="grid gap-1.5 leading-none">
                      <Label htmlFor={seq.id} className="font-bold">
                        {seq.name}
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        {seq.description}
                      </p>
                      <p className="font-mono text-sm break-all">
                        {seq.sequence}
                      </p>
                      {seq.source && (
                        <a
                          href={seq.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-500 hover:underline"
                        >
                          Source
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-end">
        {!message.isStreaming && interruptMessage?.options?.length && (
          <motion.div
            className="flex gap-2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            {interruptMessage?.options.map((option) => (
              <Button
                key={option.value}
                variant={
                  option.value === "accept_sequences" ? "default" : "outline"
                }
                disabled={
                  !waitForFeedback ||
                  (option.value === "accept_sequences" &&
                    selectedSequences.length === 0)
                }
                onClick={() => {
                  if (option.value === "accept_sequences") {
                    void handleAccept();
                  } else {
                    onFeedback?.({
                      option,
                    });
                  }
                }}
              >
                {option.text}
              </Button>
            ))}
          </motion.div>
        )}
      </CardFooter>
    </Card>
  );
}

function PodcastCard({
  className,
  message,
}: {
  className?: string;
  message: Message;
}) {
  const data = useMemo(() => {
    return JSON.parse(message.content ?? "");
  }, [message.content]);
  const title = useMemo<string | undefined>(() => data?.title, [data]);
  const audioUrl = useMemo<string | undefined>(() => data?.audioUrl, [data]);
  const isGenerating = useMemo(() => {
    return message.isStreaming;
  }, [message.isStreaming]);
  const hasError = useMemo(() => {
    return data?.error !== undefined;
  }, [data]);
  const [isPlaying, setIsPlaying] = useState(false);
  return (
    <Card className={cn("w-[508px]", className)}>
      <CardHeader>
        <div className="text-muted-foreground flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            {isGenerating ? <LoadingOutlined /> : <Headphones size={16} />}
            {!hasError ? (
              <RainbowText animated={isGenerating}>
                {isGenerating
                  ? "Generating podcast..."
                  : isPlaying
                    ? "Now playing podcast..."
                    : "Podcast"}
              </RainbowText>
            ) : (
              <div className="text-red-500">
                Error when generating podcast. Please try again.
              </div>
            )}
          </div>
          {!hasError && !isGenerating && (
            <div className="flex">
              <Tooltip title="Download podcast">
                <Button variant="ghost" size="icon" asChild>
                  <a
                    href={audioUrl}
                    download={`${(title ?? "podcast").replaceAll(" ", "-")}.mp3`}
                  >
                    <Download size={16} />
                  </a>
                </Button>
              </Tooltip>
            </div>
          )}
        </div>
        <CardTitle>
          <div className="text-lg font-medium">
            <RainbowText animated={isGenerating}>{title}</RainbowText>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {audioUrl ? (
          <audio
            className="w-full"
            src={audioUrl}
            controls
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
        ) : (
          <div className="w-full"></div>
        )}
      </CardContent>
    </Card>
  );
}
