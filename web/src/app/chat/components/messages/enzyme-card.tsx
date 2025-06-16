import { motion } from "framer-motion";
import { useCallback, useMemo } from "react";

import { Markdown } from "~/components/deer-flow/markdown";
import { RainbowText } from "~/components/deer-flow/rainbow-text";
import { RollingText } from "~/components/deer-flow/rolling-text";
import { Button } from "~/components/ui/button";
import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "~/components/ui/card";
import type { Message, Option } from "~/core/messages";
import {
    closeResearch,
    openResearch,
    useStore,
} from "~/core/store";
import { cn } from "~/lib/utils";




// ---------------- Enzyme Retriever Card ----------------
export function EnzymeRetrieverCard({
    className,
    message,
    onToggleResearch,
}: {
    className?: string;
    message: Message; // enzyme_retriever start message
    onToggleResearch?: () => void;
}) {
    const researchId = message.id;
    const openResearchId = useStore((state) => state.openResearchId);
    const isStreaming = message.isStreaming;
    const status = isStreaming ? "Retrieving sequences..." : "Sequences retrieved";

    const handleOpen = useCallback(() => {
        if (openResearchId === researchId) {
            closeResearch();
        } else {
            openResearch(researchId);
        }
        onToggleResearch?.();
    }, [openResearchId, researchId, onToggleResearch]);

    return (
        <Card className={cn("w-full", className)}>
            <CardHeader>
                <CardTitle>
                    <RainbowText animated={isStreaming}>酶序列挖掘</RainbowText>
                </CardTitle>
            </CardHeader>
            <CardFooter>
                <div className="flex w-full">
                    <RollingText className="text-muted-foreground flex-grow text-sm">
                        {status}
                    </RollingText>
                    <Button
                        variant={!openResearchId ? "default" : "outline"}
                        onClick={handleOpen}
                    >
                        {researchId !== openResearchId ? "Open" : "Close"}
                    </Button>
                </div>
            </CardFooter>
        </Card>
    );
}

// ==================== Enzyme Selection Card ====================
export function EnzymeSelectionCard({
    className,
    interruptMessage,
    waitForFeedback,
    onFeedback,
}: {
    className?: string;
    interruptMessage: Message;
    waitForFeedback?: boolean;
    onFeedback?: (feedback: { option: Option }) => void;
}) {
    // Extract sequences from extra_data
    const sequences = useMemo(() => {
        try {
            return interruptMessage.extra_data?.sequences ?? [];
        } catch {
            return [];
        }
    }, [interruptMessage.extra_data]);

    return (
        <Card className={cn("w-full", className)}>
            <CardHeader>
                <CardTitle>
                    <Markdown animated>{`### 🧬 Review Enzyme Sequences`}</Markdown>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <Markdown className="opacity-80" animated>
                    {interruptMessage.content}
                </Markdown>
                {Array.isArray(sequences) && sequences.length > 0 && (
                    <ul className="mt-4 flex max-h-[320px] flex-col gap-4 overflow-y-auto pr-2">
                        {sequences.map((seq: any, i: number) => (
                            <li
                                key={`enzyme-seq-${i}`}
                                className="bg-accent/20 rounded-md p-3 text-sm"
                            >
                                {seq.protein_name && (
                                    <div className="font-medium">{seq.protein_name}</div>
                                )}
                                {seq.sequence && (
                                    <div className="font-mono break-all text-xs">
                                        {seq.sequence.length > 120
                                            ? `${seq.sequence.slice(0, 120)}...`
                                            : seq.sequence}
                                    </div>
                                )}
                                <div className="text-muted-foreground mt-1 flex flex-wrap gap-2 text-xs">
                                    {seq.organism_name && (
                                        <span>Organism: {seq.organism_name}</span>
                                    )}
                                    {seq.accession && <span>Accession: {seq.accession}</span>}
                                    {seq.gene_name && <span>Gene: {seq.gene_name}</span>}
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </CardContent>
            <CardFooter className="flex justify-end">
                {!interruptMessage.isStreaming && interruptMessage?.options?.length && (
                    <motion.div
                        className="flex gap-2"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: 0.3 }}
                    >
                        {interruptMessage.options.map((option) => (
                            <Button
                                key={option.value}
                                variant={option.value === "accept_sequences" ? "default" : "outline"}
                                disabled={!waitForFeedback}
                                onClick={() => {
                                    onFeedback?.({ option });
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