// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import mermaid from 'mermaid';
import type { MermaidConfig, RunOptions } from 'mermaid';
import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { useTheme } from 'next-themes';
import { ZoomInIcon, ZoomOutIcon, DownloadIcon, Copy, Check } from 'lucide-react';

interface MermaidProps {
    chart: string; // The Mermaid code string
    isStreaming?: boolean;
}

// Define available Mermaid themes
// Standard themes: 'default', 'dark', 'neutral', 'forest'
const mermaidThemes = [
    { name: 'Default', value: 'default' },
    { name: 'Dark', value: 'dark' },
    { name: 'Neutral', value: 'neutral' },
    { name: 'Forest', value: 'forest' },
] as const;

type MermaidThemeValue = typeof mermaidThemes[number]['value'];
type ViewMode = 'diagram' | 'code';

const MermaidDiagram: React.FC<MermaidProps> = ({ chart, isStreaming = false }) => {
    const elementRef = useRef<HTMLDivElement>(null); // Where Mermaid actually renders its SVG
    const svgContainerRef = useRef<HTMLDivElement>(null); // Parent for zoom and fixed size viewport
    const { resolvedTheme: hostTheme } = useTheme();
    const [selectedMermaidTheme, setSelectedMermaidTheme] = useState<MermaidThemeValue>('default');
    const [zoomLevel, setZoomLevel] = useState(0.75);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [startPanPosition, setStartPanPosition] = useState({ x: 0, y: 0 });
    const [diagramId] = useState(() => `mermaid-diagram-${Math.random().toString(36).substring(7)}`);
    const [viewMode, setViewMode] = useState<ViewMode>('diagram');
    const [copied, setCopied] = useState(false);

    const fixedChart = useMemo(() => {
        return chart.replace(/“/g, '"')
            .replace(/”/g, '"')
            .replace(/：/g, ':');
    }, [chart]);

    const handleCopyCode = useCallback(() => {
        if (!fixedChart) return;
        navigator.clipboard.writeText(fixedChart).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }).catch(err => {
            console.error('Failed to copy code: ', err);
        });
    }, [fixedChart]);

    const handleDownloadCode = useCallback(() => {
        if (!fixedChart) return;
        const blob = new Blob([fixedChart], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'mermaid-code.txt';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }, [fixedChart]);

    // Apply combined transformations (pan and zoom)
    const applyTransformations = useCallback(() => {
        if (elementRef.current) {
            // The elementRef (actual diagram content) is panned and zoomed.
            elementRef.current.style.transform = `translate(${pan.x}px, ${pan.y}px) scale(${zoomLevel})`;
            elementRef.current.style.transformOrigin = 'top left';
        }
        if (svgContainerRef.current) {
            // The svgContainerRef (viewport) is not scaled, so remove any transform.
            svgContainerRef.current.style.transform = '';
        }
    }, [pan, zoomLevel]);

    useEffect(() => {
        applyTransformations();
    }, [pan, zoomLevel, applyTransformations]);

    // Handle background color for the viewport based on theme
    useEffect(() => {
        if (svgContainerRef.current) {
            if (selectedMermaidTheme === 'dark') {
                svgContainerRef.current.style.backgroundColor = '#1a1a1a'; // Dark background for viewport
            } else {
                svgContainerRef.current.style.backgroundColor = '#ffffff'; // White background for viewport for other themes
            }
        }
    }, [selectedMermaidTheme]);

    useEffect(() => {
        if (viewMode !== 'diagram') {
            return;
        }
        // Mermaid.js only works in the browser
        if (typeof window === 'undefined' || !elementRef.current || !svgContainerRef.current) {
            return;
        }

        const currentElement = elementRef.current;
        let themeForMermaid: MermaidThemeValue = selectedMermaidTheme;
        let effectiveThemeVariables: MermaidConfig['themeVariables'] = {
            mainBkg: 'transparent', // Ensure diagram background is transparent by default
        };

        if (themeForMermaid === 'dark') {
            effectiveThemeVariables = {
                mainBkg: '#1a1a1a', // Mermaid internal background for dark themes
                textColor: '#e5e7eb',
                primaryTextColor: '#f3f4f6',
                secondaryTextColor: '#d1d5db',
                lineColor: '#9ca3af',
                borderColor: '#6b7280',
                primaryColor: '#374151', // Node background in some cases
                primaryBorderColor: '#9ca3af',
                secondaryColor: '#4b5563',
                tertiaryColor: '#52525b',
                actorText: '#e5e7eb',
                taskText: '#e5e7eb',
                pieTitleText: '#f9fafb',
                pieSectionText: '#e5e7eb',
                labelTextColor: '#e5e7eb',
                classText: '#e5e7eb',
                messageText: '#e5e7eb',
                noteText: '#e5e7eb',
                gitGraphText: '#e5e7eb',
                sectionTitleColor: '#f9fafb',
                legendTextColor: '#e5e7eb',
                nodeBkg: '#374151',
                actorBkg: '#374151',
                clusterBkg: '#4b5563',
                altBackground: '#4b5563',
                // Color palette for diagrams
                pie1: '#60a5fa', pie2: '#f87171', pie3: '#4ade80', pie4: '#fbbf24',
                pie5: '#a78bfa', pie6: '#22d3ee', pie7: '#f472b6', pie8: '#818cf8',
                pie9: '#c084fc', pie10: '#fb923c', pie11: '#a3e635', pie12: '#34d399',
            };
        } else {
            // For 'default', 'neutral', 'forest'
            effectiveThemeVariables = {
                mainBkg: 'transparent', // Mermaid elements should have transparent background to show viewport bg
                textColor: hostTheme === 'dark' && themeForMermaid !== 'forest' ? '#ccc' : '#1f2937',
                primaryTextColor: hostTheme === 'dark' && themeForMermaid !== 'forest' ? '#eee' : '#111827',
                lineColor: hostTheme === 'dark' && themeForMermaid !== 'forest' ? '#aaa' : '#d1d5db',
            };
            if (themeForMermaid === 'forest') {
                effectiveThemeVariables.mainBkg = '#2b2b2b'; // Forest theme specific background for its elements
                effectiveThemeVariables.textColor = '#e0e0e0';
                // if svgContainerRef is white, forest mainBkg will sit on top.
            }
        }

        mermaid.initialize({
            startOnLoad: false,
            theme: themeForMermaid,
            // themeVariables: effectiveThemeVariables,
            securityLevel: 'loose', // Consider if needed
        } as MermaidConfig);

        const renderMermaid = async () => {
            const defaultZoom = 0.75;
            setZoomLevel(defaultZoom);

            if (fixedChart && fixedChart.trim() !== "" && currentElement) {
                if (isStreaming) {
                    // During streaming, we can expect incomplete diagrams. Show something less intrusive.
                    currentElement.innerHTML = `<pre class="text-yellow-500">Waiting for complete Mermaid code...\n\n${fixedChart}</pre>`;
                    return
                }
                try {
                    // Render SVG in memory and place it into the container
                    const { svg } = await mermaid.render(diagramId, fixedChart);
                    currentElement.innerHTML = svg;

                    // Center the diagram after rendering
                    const svgElement = currentElement.querySelector('svg');
                    if (svgElement && svgContainerRef.current) {
                        const containerRect = svgContainerRef.current.getBoundingClientRect();
                        const svgBBox = (svgElement as SVGSVGElement).getBBox();
                        const svgWidth = svgBBox.width;
                        const svgHeight = svgBBox.height;

                        const initialPanX = (containerRect.width - svgWidth * defaultZoom) / 2;
                        const initialPanY = (containerRect.height - svgHeight * defaultZoom) / 2;

                        setPan({ x: initialPanX, y: initialPanY });
                    }
                } catch (error) {
                    console.error("Mermaid rendering error:", error);
                    const errorMessage = error instanceof Error ? error.message : String(error);
                    currentElement.innerHTML = `<pre class="text-red-500">Error rendering Mermaid diagram:\n${errorMessage}\n\n${fixedChart}</pre>`;
                }
            } else if (currentElement) {
                currentElement.innerHTML = ""; // Clear if no chart code
                setPan({ x: 0, y: 0 }); // Reset pan if no chart
            }
        };

        renderMermaid();

    }, [fixedChart, selectedMermaidTheme, hostTheme, diagramId, isStreaming, viewMode]);

    const handleZoomIn = () => setZoomLevel(prev => Math.min(prev * 1.2, 3));
    const handleZoomOut = () => setZoomLevel(prev => Math.max(prev / 1.2, 0.5));

    const handleMouseDown = (e: React.MouseEvent) => {
        if (!elementRef.current || !svgContainerRef.current) return;
        // Prevent text selection while dragging
        e.preventDefault();
        setIsPanning(true);
        // Calculate mouse position relative to the viewport.
        const rect = svgContainerRef.current.getBoundingClientRect();
        const initialMouseX = e.clientX - rect.left;
        const initialMouseY = e.clientY - rect.top;
        setStartPanPosition({
            x: initialMouseX - pan.x,
            y: initialMouseY - pan.y,
        });
        svgContainerRef.current.style.cursor = 'grabbing';
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isPanning || !svgContainerRef.current) return;
        const rect = svgContainerRef.current.getBoundingClientRect();
        const currentMouseX = e.clientX - rect.left;
        const currentMouseY = e.clientY - rect.top;
        setPan({
            x: currentMouseX - startPanPosition.x,
            y: currentMouseY - startPanPosition.y,
        });
    };

    const handleMouseUpOrLeave = () => {
        if (isPanning) {
            setIsPanning(false);
            if (svgContainerRef.current) {
                svgContainerRef.current.style.cursor = 'grab';
            }
        }
    };

    const handleDownloadSvg = async () => {
        if (!elementRef.current || !fixedChart.trim()) return;

        try {
            // Temporarily render SVG to get the string
            // Note: mermaid.render is tricky to use directly for download without a visible element sometimes.
            // An alternative is to grab the innerHTML of the rendered SVG.
            const svgElement = elementRef.current.querySelector(`svg`);
            if (svgElement) {
                const svgData = new XMLSerializer().serializeToString(svgElement);
                const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'mermaid-diagram.svg';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            } else {
                console.error("Could not find rendered SVG element to download.");
                // Fallback or error message
                alert("Error: Could not prepare diagram for download. SVG not found.");
            }
        } catch (error) {
            console.error("Mermaid download error:", error);
            alert(`Error preparing download: ${error instanceof Error ? error.message : String(error)}`);
        }
    };

    // This div will contain the Mermaid diagram SVG output and controls
    return (
        <div className="mermaid-diagram-wrapper my-4 overflow-hidden rounded-lg border">
            {/* Header */}
            <div className="flex items-center justify-between border-b bg-gray-50 p-2 dark:border-gray-700 dark:bg-gray-800">
                {/* Left: View toggle */}
                <div className="inline-flex items-center rounded-md bg-gray-200 p-1 dark:bg-gray-700">
                    <button
                        onClick={() => setViewMode('diagram')}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${viewMode === 'diagram' ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white font-semibold shadow' : 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'}`}
                    >
                        图表
                    </button>
                    <button
                        onClick={() => setViewMode('code')}
                        className={`px-3 py-1 text-sm rounded-md transition-colors ${viewMode === 'code' ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white font-semibold shadow' : 'bg-transparent text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'}`}
                    >
                        代码
                    </button>
                </div>
                {/* Right: Controls */}
                <div className="flex items-center space-x-2">
                    {viewMode === 'diagram' && (
                        <>
                            <select
                                value={selectedMermaidTheme}
                                onChange={(e) => setSelectedMermaidTheme(e.target.value as MermaidThemeValue)}
                                className="p-1 border rounded text-xs bg-gray-50 dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                                title="Select Theme"
                            >
                                {mermaidThemes.map(theme => (
                                    <option key={theme.name} value={theme.value}>{theme.name}</option>
                                ))}
                            </select>
                            <button onClick={handleZoomIn} className="rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-600" title="Zoom In">
                                <ZoomInIcon size={18} />
                            </button>
                            <button onClick={handleZoomOut} className="rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-600" title="Zoom Out">
                                <ZoomOutIcon size={18} />
                            </button>
                            <button onClick={handleDownloadSvg} className="rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-600" title="Download SVG">
                                <DownloadIcon size={18} />
                            </button>
                        </>
                    )}
                    {viewMode === 'code' && (
                        <>
                            <button onClick={handleCopyCode} className="rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-700" title="Copy">
                                {copied ? <Check size={18} /> : <Copy size={18} />}
                            </button>
                            <button onClick={handleDownloadCode} className="rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-700" title="Download Code">
                                <DownloadIcon size={18} />
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Content */}
            {viewMode === 'diagram' ? (
                <div
                    ref={svgContainerRef}
                    className="mermaid-zoom-container relative h-[400px] w-full cursor-grab overflow-hidden" // Fixed height, overflow hidden, cursor
                    style={{ backgroundColor: 'white' }} // Default background, will be updated by useEffect
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUpOrLeave}
                    onMouseLeave={handleMouseUpOrLeave} // Stop panning if mouse leaves container
                >
                    {/* This inner container holds the actual Mermaid SVG and is panned (translated) */}
                    <div ref={elementRef} className="mermaid-diagram-container w-full" />
                </div>
            ) : (
                <div className="h-[400px] overflow-auto bg-gray-50 dark:bg-gray-900">
                    <pre className="h-full p-4 text-sm">
                        <code className="language-mermaid">{fixedChart}</code>
                    </pre>
                </div>
            )}
        </div>
    );
};

export default MermaidDiagram; 