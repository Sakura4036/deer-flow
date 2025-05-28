// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { useEffect, useRef, useState } from "react";

import { useReplay } from "../replay";

import { fetchReplayList, fetchReplayTitle } from "./chat";

export function useReplayMetadata() {
  const { isReplay } = useReplay();
  const [title, setTitle] = useState<string | null>(null);
  const isLoading = useRef(false);
  const [error, setError] = useState<boolean>(false);
  useEffect(() => {
    if (!isReplay) {
      return;
    }
    if (title || isLoading.current) {
      return;
    }
    isLoading.current = true;
    fetchReplayTitle()
      .then((title) => {
        console.log("useReplayMetadata title: ", title);
        setError(false);
        setTitle(title ?? null);
        if (title) {
          document.title = `${title} - DeerFlow`;
        }
      })
      .catch(() => {
        console.log("useReplayMetadata error: ", error);
        setError(true);
        setTitle("Error: the replay is not available.");
        document.title = "DeerFlow";
      })
      .finally(() => {
        isLoading.current = false;
      });
  }, [isLoading, isReplay, title]);
  return { title, isLoading, hasError: error };
}

export function useReplayList() {
  const [replays, setReplays] = useState<Array<{
    id: string;
    title: string;
    created_at: number;
    size: number;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReplays = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchReplayList();
      setReplays(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch replays");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReplays();
  }, []);

  return { replays, isLoading, error, refetch: fetchReplays };
}
