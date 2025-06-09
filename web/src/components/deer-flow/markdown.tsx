// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { Check, Copy } from "lucide-react";
import { useMemo, useState } from "react";
import ReactMarkdown, {
  type Options as ReactMarkdownOptions,
} from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

import { Button } from "~/components/ui/button";
import { rehypeSplitWordsIntoSpans } from "~/core/rehype";
import { autoFixMarkdown } from "~/core/utils/markdown";
import { cn } from "~/lib/utils";

import Image from "./image";
import { Tooltip } from "./tooltip";
import { Link } from "./link";
import MermaidDiagram from "./mermaid-diagram";

// Define a type for the props of the custom code component
interface CustomCodeProps {
  node?: any; // Consider using a more specific type from ReactMarkdown if available
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
  // Include any other props that ReactMarkdown might pass to the code component
  [key: string]: any;
}

export function Markdown({
  className,
  children,
  style,
  enableCopy,
  animated = false,
  checkLinkCredibility = false,
  isStreaming = false,
  ...props
}: ReactMarkdownOptions & {
  className?: string;
  enableCopy?: boolean;
  style?: React.CSSProperties;
  animated?: boolean;
  checkLinkCredibility?: boolean;
  isStreaming?: boolean;
}) {
  const processedMarkdown = useMemo(
    () =>
      autoFixMarkdown(
        dropMarkdownQuote(processKatexInMarkdown(children ?? "")) ?? "",
      ),
    [children],
  );

  const components: ReactMarkdownOptions["components"] = useMemo(() => {
    return {
      a: ({ href, children: linkChildren }) => ( // Renamed children to avoid conflict
        <Link href={href} checkLinkCredibility={checkLinkCredibility}>
          {linkChildren}
        </Link>
      ),
      img: ({ src, alt }) => (
        <a href={src as string} target="_blank" rel="noopener noreferrer">
          <Image className="rounded" src={src as string} alt={alt ?? ""} />
        </a>
      ),
      // Add custom renderer for code blocks
      code({
        inline,
        className: codeClassName,
        children: codeChildren,
        ...codeProps
      }: CustomCodeProps) {
        const match = /language-(\w+)/.exec(codeClassName || "");
        if (!inline && match && match[1] === "mermaid") {
          return (
            <MermaidDiagram
              chart={String(codeChildren).trim()}
              isStreaming={isStreaming}
            />
          );
        }
        return inline ? (
          <code className={codeClassName} {...codeProps}>
            {codeChildren}
          </code>
        ) : (
          <pre
            className={cn(
              codeClassName,
              "p-4 rounded-md overflow-x-auto",
            )}
            {...(codeProps as React.HTMLAttributes<HTMLPreElement>)}
          >
            <code className="text-sm">{codeChildren}</code>
          </pre>
        );
      },
    };
  }, [checkLinkCredibility, isStreaming]);

  const rehypePlugins = useMemo(() => {
    const plugins: any[] = [rehypeKatex];
    if (animated) {
      plugins.splice(1, 0, rehypeSplitWordsIntoSpans);
    }
    return plugins;
  }, [animated]);

  return (
    <div className={cn(className, "prose dark:prose-invert")} style={style}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={rehypePlugins}
        components={components}
        {...props}
      >
        {processedMarkdown}
      </ReactMarkdown>
      {enableCopy && typeof children === "string" && (
        <div className="flex">
          <CopyButton content={children} />
        </div>
      )}
    </div>
  );
}

function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Tooltip title="Copy">
      <Button
        variant="outline"
        size="sm"
        className="rounded-full"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(content);
            setCopied(true);
            setTimeout(() => {
              setCopied(false);
            }, 1000);
          } catch (error) {
            console.error(error);
          }
        }}
      >
        {copied ? (
          <Check className="h-4 w-4" />
        ) : (
          <Copy className="h-4 w-4" />
        )}{" "}
      </Button>
    </Tooltip>
  );
}

function processKatexInMarkdown(markdown?: string | null) {
  if (!markdown) return markdown;

  const markdownWithKatexSyntax = markdown
    .replace(/\\\\\[/g, "$$$$") // Replace '\\[' with '$$'
    .replace(/\\\\\]/g, "$$$$") // Replace '\\]' with '$$'
    .replace(/\\\\\(/g, "$$$$") // Replace '\\(' with '$$'
    .replace(/\\\\\)/g, "$$$$") // Replace '\\)' with '$$'
    .replace(/\\\[/g, "$$$$") // Replace '\[' with '$$'
    .replace(/\\\]/g, "$$$$") // Replace '\]' with '$$'
    .replace(/\\\(/g, "$$$$") // Replace '\(' with '$$'
    .replace(/\\\)/g, "$$$$"); // Replace '\)' with '$$';
  return markdownWithKatexSyntax;
}

function dropMarkdownQuote(markdown?: string | null) {
  if (!markdown) return markdown;
  // Only remove a ```markdown or ```text block if it truly wraps the entire content.
  // This is a simplified check. A more robust solution might involve parsing.
  let newMarkdown = markdown;
  if (
    (newMarkdown.startsWith("```markdown\n") && newMarkdown.endsWith("\n```")) ||
    (newMarkdown.startsWith("```text\n") && newMarkdown.endsWith("\n```"))
  ) {
    if (newMarkdown.startsWith("```markdown\n")) {
      newMarkdown = newMarkdown.substring("```markdown\n".length);
    } else if (newMarkdown.startsWith("```text\n")) {
      newMarkdown = newMarkdown.substring("```text\n".length);
    }
    if (newMarkdown.endsWith("\n```")) {
      newMarkdown = newMarkdown.substring(0, newMarkdown.length - "\n```".length);
    }
    return newMarkdown;
  }

  // The original broader replacements, which might be problematic:
  // return markdown
  //   .replace(/^```markdown\n/gm, "")
  //   .replace(/^```text\n/gm, "")
  //   .replace(/^```\n/gm, "") // This was likely too broad
  //   .replace(/\n```$/gm, ""); // This was also likely too broad
  return markdown; // Return original markdown if not a full wrapper
}
