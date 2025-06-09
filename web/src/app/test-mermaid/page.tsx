"use client"; // Required for components using hooks like useEffect

import React, { useEffect, useState } from 'react';
import { Markdown } from "~/components/deer-flow/markdown"; // Adjust path if necessary

export default function TestMermaidPage() {
    const [mermaidTestMarkdown, setMermaidTestMarkdown] = useState('');
    const [isStreaming, setIsStreaming] = useState(true);

    useEffect(() => {
        fetch('/enzyme.md')
            .then((res) => res.text())
            .then((text) => {
                const lines = text.split('\n');
                let currentIndex = 0;
                const interval = setInterval(() => {
                    if (currentIndex < lines.length) {
                        setMermaidTestMarkdown((prev) => prev + lines[currentIndex] + '\n');
                        currentIndex++;
                    } else {
                        setIsStreaming(false);
                        clearInterval(interval);
                    }
                }, 100); // stream line by line
            })
            .catch((err) => {
                console.error('Failed to load markdown file:', err);
                setIsStreaming(false);
            });
    }, []);

    return (
        <div style={{ padding: "20px" }}>
            <h1>Mermaid Test (Streaming)</h1>
            <Markdown isStreaming={isStreaming}>{mermaidTestMarkdown}</Markdown>
        </div>
    );
} 