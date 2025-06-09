"use client";

import { StagewiseToolbar } from "@stagewise/toolbar-next";
import { useSearchParams } from "next/navigation";

// Stagewise toolbar for AI interaction
export function StagewiseProvider() {
    const searchParams = useSearchParams();
    const isStagewiseIframe = searchParams.get("iframe") === "stagewise";

    if (process.env.NODE_ENV === "development" && !isStagewiseIframe) {
        return <StagewiseToolbar />;
    }

    return null;
} 