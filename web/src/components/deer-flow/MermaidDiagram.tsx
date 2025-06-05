// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import mermaid from 'mermaid';
import type { MermaidConfig, RunOptions } from 'mermaid';
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTheme } from 'next-themes';
import { ZoomInIcon, ZoomOutIcon, DownloadIcon } from 'lucide-react';

interface MermaidProps {
    chart: string; // The Mermaid code string
}

// Define available Mermaid themes
// 'Neo' and 'Deo Dark' are not standard Mermaid themes. We'll map them or use 'default'/'dark' as fallback.
// Standard themes: 'default', 'dark', 'neutral', 'forest'
const mermaidThemes = [
    { name: 'Default', value: 'default' },
    { name: 'Dark', value: 'dark' },
    { name: 'Neutral', value: 'neutral' },
    { name: 'Forest', value: 'forest' },
    { name: 'Neo', value: 'default' }, // Placeholder, map to 'default' or a custom config
    { name: 'Deo Dark', value: 'dark' }, // Placeholder, map to 'dark' or a custom config
] as const;

type MermaidThemeValue = typeof mermaidThemes[number]['value'];

const MermaidDiagram: React.FC<MermaidProps> = ({ chart }) => {
    const elementRef = useRef<HTMLDivElement>(null); // Where Mermaid actually renders its SVG
    const svgContainerRef = useRef<HTMLDivElement>(null); // Parent for zoom and fixed size viewport
    const { resolvedTheme: hostTheme } = useTheme();
    const [selectedMermaidTheme, setSelectedMermaidTheme] = useState<MermaidThemeValue>('default');
    const [zoomLevel, setZoomLevel] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [startPanPosition, setStartPanPosition] = useState({ x: 0, y: 0 });
    const [diagramId] = useState(() => `mermaid-diagram-${Math.random().toString(36).substring(7)}`);

    // Apply combined transformations (pan and zoom)
    const applyTransformations = useCallback(() => {
        if (elementRef.current) {
            // The elementRef (actual diagram content) is panned.
            // The svgContainerRef (viewport) is scaled.
            elementRef.current.style.transform = `translate(${pan.x}px, ${pan.y}px)`;
        }
        if (svgContainerRef.current) {
            // Scale is applied to the viewport. Content inside (elementRef) is panned.
            svgContainerRef.current.style.transform = `scale(${zoomLevel})`;
            svgContainerRef.current.style.transformOrigin = 'top left'; // Or center if preferred
        }
    }, [pan, zoomLevel]);

    useEffect(() => {
        applyTransformations();
    }, [pan, zoomLevel, applyTransformations]);

    // Handle background color for the viewport based on theme
    useEffect(() => {
        if (svgContainerRef.current) {
            if (selectedMermaidTheme === 'dark') { // Includes 'Deo Dark' due to mapping
                svgContainerRef.current.style.backgroundColor = '#1a1a1a'; // Dark background for viewport
            } else {
                svgContainerRef.current.style.backgroundColor = '#ffffff'; // White background for viewport for other themes
            }
        }
    }, [selectedMermaidTheme]);

    useEffect(() => {
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
            // For 'default', 'neutral', 'forest', 'Neo'
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
            themeVariables: effectiveThemeVariables,
            // securityLevel: 'loose', // Consider if needed
        } as MermaidConfig);

        const renderMermaid = async () => {
            if (chart && chart.trim() !== "" && currentElement) {
                try {
                    // Ensure the div for mermaid to render into exists and is correctly identified
                    currentElement.innerHTML = `<div class="mermaid" id="${diagramId}">${chart}</div>`;
                    currentElement.removeAttribute('data-processed'); // Allow re-rendering by Mermaid

                    // Pass the actual DOM node to mermaid.run
                    const diagramNode = currentElement.querySelector<HTMLElement>(`#${diagramId}`);
                    if (diagramNode) {
                        await mermaid.run({ nodes: [diagramNode] } as RunOptions);
                        // Reset pan on new chart or theme to avoid showing empty space initially
                        setPan({ x: 0, y: 0 });
                        applyTransformations(); // Apply initial transformations
                    } else {
                        throw new Error("Mermaid diagram node not found after innerHTML set.");
                    }
                } catch (error) {
                    console.error("Mermaid rendering error:", error);
                    const errorMessage = error instanceof Error ? error.message : String(error);
                    currentElement.innerHTML = `<pre class="text-red-500">Error rendering Mermaid diagram:\n${errorMessage}\n\n${chart}</pre>`;
                }
            } else if (currentElement) {
                currentElement.innerHTML = ""; // Clear if no chart code
            }
        };

        renderMermaid();

    }, [chart, selectedMermaidTheme, hostTheme, applyTransformations, diagramId]);

    const handleZoomIn = () => setZoomLevel(prev => Math.min(prev * 1.2, 3));
    const handleZoomOut = () => setZoomLevel(prev => Math.max(prev / 1.2, 0.5));

    const handleMouseDown = (e: React.MouseEvent) => {
        if (!elementRef.current || !svgContainerRef.current) return;
        // Prevent text selection while dragging
        e.preventDefault();
        setIsPanning(true);
        // Calculate mouse position relative to the scaled and panned element for consistent panning
        const rect = svgContainerRef.current.getBoundingClientRect();
        const initialMouseX = (e.clientX - rect.left) / zoomLevel;
        const initialMouseY = (e.clientY - rect.top) / zoomLevel;
        setStartPanPosition({
            x: initialMouseX - pan.x,
            y: initialMouseY - pan.y,
        });
        svgContainerRef.current.style.cursor = 'grabbing';
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isPanning || !svgContainerRef.current) return;
        const rect = svgContainerRef.current.getBoundingClientRect();
        const currentMouseX = (e.clientX - rect.left) / zoomLevel;
        const currentMouseY = (e.clientY - rect.top) / zoomLevel;
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

    const handleDownload = async () => {
        if (!elementRef.current || !chart.trim()) return;

        try {
            // Temporarily render SVG to get the string
            // Note: mermaid.render is tricky to use directly for download without a visible element sometimes.
            // An alternative is to grab the innerHTML of the rendered SVG.
            const svgElement = elementRef.current.querySelector(`#${diagramId} > svg`);
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
        <div className="mermaid-diagram-wrapper relative group">
            <div className="mermaid-controls absolute top-2 right-2 z-10 hidden group-hover:flex items-center space-x-2 bg-white dark:bg-gray-800 p-1 rounded shadow">
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
                <button onClick={handleZoomIn} className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="Zoom In">
                    <ZoomInIcon size={18} />
                </button>
                <button onClick={handleZoomOut} className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="Zoom Out">
                    <ZoomOutIcon size={18} />
                </button>
                <button onClick={handleDownload} className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded" title="Download SVG">
                    <DownloadIcon size={18} />
                </button>
            </div>
            {/* This container handles zoom, has fixed size, and hides overflow. It's also the target for mouse events for panning. */}
            <div
                ref={svgContainerRef}
                className="mermaid-zoom-container relative w-full h-[400px] border rounded overflow-hidden cursor-grab" // Fixed height, overflow hidden, cursor
                style={{ backgroundColor: 'white' }} // Default background, will be updated by useEffect
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUpOrLeave}
                onMouseLeave={handleMouseUpOrLeave} // Stop panning if mouse leaves container
            >
                {/* This inner container holds the actual Mermaid SVG and is panned (translated) */}
                <div ref={elementRef} className="mermaid-diagram-container w-full" />
            </div>
        </div>
    );
};

export default MermaidDiagram; 