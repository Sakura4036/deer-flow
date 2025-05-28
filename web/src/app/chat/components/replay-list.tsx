// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";

import { useReplayList } from "~/core/api/hooks";
import { Button } from "~/components/ui/button";
import { Skeleton } from "~/components/ui/skeleton";
import { cn } from "~/lib/utils";

// Component for showing replay items
export function ReplayList({ className }: { className?: string }) {
    const { replays, isLoading, error, refetch } = useReplayList();
    const [isVisible, setIsVisible] = useState(true);
    const router = useRouter();

    // Format date for display
    const formatDate = (timestamp: number) => {
        return format(new Date(timestamp * 1000), "yyyy-MM-dd HH:mm");
    };

    // Format file size for display
    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    if (!isVisible) {
        return (
            <div className="fixed left-0 top-16 z-10">
                <Button
                    variant="ghost"
                    className="rounded-r-full rounded-l-none p-2 bg-secondary"
                    onClick={() => setIsVisible(true)}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="m9 18 6-6-6-6" />
                    </svg>
                </Button>
            </div>
        );
    }

    return (
        <div className={cn("fixed left-0 top-16 z-10 h-[calc(100vh-4rem)] w-64 bg-card border-r border-border overflow-hidden transition-all duration-300", className)}>
            <div className="flex justify-between items-center p-3 border-b border-border">
                <h3 className="font-medium text-sm">回放列表</h3>
                <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={refetch} title="刷新">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                            <path d="M3 3v5h5" />
                        </svg>
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => setIsVisible(false)} title="隐藏">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="m15 18-6-6 6-6" />
                        </svg>
                    </Button>
                </div>
            </div>

            <div className="overflow-y-auto h-full p-2">
                {isLoading ? (
                    <div className="space-y-2">
                        {Array(5).fill(0).map((_, i) => (
                            <div key={i} className="flex flex-col gap-1 p-2">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-3 w-3/4" />
                            </div>
                        ))}
                    </div>
                ) : error ? (
                    <div className="text-center p-4 text-destructive">
                        <p>加载失败</p>
                        <Button variant="outline" size="sm" onClick={refetch} className="mt-2">
                            重试
                        </Button>
                    </div>
                ) : replays.length === 0 ? (
                    <div className="text-center p-4 text-muted-foreground">
                        <p>暂无回放记录</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {replays.map((replay) => (
                            <Link
                                href={`/chat?replay=${replay.id}`}
                                key={replay.id}
                                className="block p-2 rounded-md hover:bg-accent transition-colors"
                                onClick={() => {
                                    console.log(`Loading replay: ${replay.id}`);
                                    // 可以在这里添加加载状态或其他反馈
                                }}
                            >
                                <div className="text-sm font-medium truncate" title={replay.title}>
                                    {replay.title}
                                </div>
                                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                    <span>{formatDate(replay.created_at)}</span>
                                    <span>{formatSize(replay.size)}</span>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
} 