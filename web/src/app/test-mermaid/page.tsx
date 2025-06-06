"use client"; // Required for components using hooks like useEffect

import React, { useEffect, useState } from 'react';
import { Markdown } from "~/components/deer-flow/markdown"; // Adjust path if necessary

export default function TestMermaidPage() {
    const [mermaidTestMarkdown, setMermaidTestMarkdown] = useState('');

    useEffect(() => {
        fetch('/enzyme.md')
            .then((res) => res.text())
            .then((text) => {
                setMermaidTestMarkdown(text);
            })
            .catch((err) => {
                console.error('Failed to load markdown file:', err);
            });
    }, []);

    return (
        <div style={{ padding: "20px" }}>
            <h1>Mermaid Test</h1>
            <Markdown>{mermaidTestMarkdown}</Markdown>
        </div>
    );
} 