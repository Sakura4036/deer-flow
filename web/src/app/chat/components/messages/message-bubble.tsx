
import type { Message } from "~/core/messages";
import { cn } from "~/lib/utils";

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

export default MessageBubble;