"use client";

import { useEffect, useRef } from "react";

import type { Message } from "@/lib/api";

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function deliveryLabel(status: string, error: string) {
  if (status === "sending") {
    return "Sending...";
  }
  if (status === "failed") {
    return error || "Failed to send";
  }
  if (status === "sent") {
    return "Sent";
  }
  return "";
}

type MessageThreadProps = {
  messages: Message[];
  isRefreshing?: boolean;
};

export function MessageThread({ messages, isRefreshing }: MessageThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <p className="text-sm text-zinc-500">No messages yet. Send a reply to start.</p>
      </div>
    );
  }

  return (
    <div className="relative flex-1 overflow-y-auto p-5">
      {isRefreshing && (
        <p className="mb-3 text-center text-xs text-zinc-400">Checking for new messages...</p>
      )}

      <div className="space-y-4">
        {messages.map((message) => {
          const isOutbound = message.direction === "outbound";
          return (
            <div
              key={message.id}
              className={`flex ${isOutbound ? "justify-end" : "justify-start"}`}
            >
              <div className={`max-w-[85%] ${isOutbound ? "items-end" : "items-start"}`}>
                <p
                  className={`mb-1 text-[10px] font-semibold uppercase tracking-wide ${
                    isOutbound ? "text-right text-zinc-400" : "text-zinc-500"
                  }`}
                >
                  {isOutbound ? "You" : "Client"}
                </p>
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                    isOutbound
                      ? "rounded-br-md bg-zinc-900 text-white"
                      : "rounded-bl-md bg-zinc-100 text-zinc-900 ring-1 ring-zinc-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">{message.content}</p>
                  <div
                    className={`mt-1.5 flex flex-wrap items-center gap-1 text-[11px] ${
                      isOutbound ? "text-zinc-300" : "text-zinc-500"
                    }`}
                  >
                    <span>{formatTime(message.sent_at)}</span>
                    {isOutbound && message.delivery_status && (
                      <>
                        <span>·</span>
                        <span
                          className={
                            message.delivery_status === "failed"
                              ? "text-red-300"
                              : undefined
                          }
                        >
                          {deliveryLabel(
                            message.delivery_status,
                            message.delivery_error,
                          )}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}

export function MessageThreadSkeleton() {
  return (
    <div className="flex-1 space-y-4 overflow-y-auto p-5">
      <div className="flex justify-start">
        <div className="h-16 w-2/3 max-w-sm animate-pulse rounded-2xl bg-zinc-100" />
      </div>
      <div className="flex justify-end">
        <div className="h-14 w-1/2 max-w-xs animate-pulse rounded-2xl bg-zinc-200" />
      </div>
      <div className="flex justify-start">
        <div className="h-20 w-3/5 max-w-md animate-pulse rounded-2xl bg-zinc-100" />
      </div>
    </div>
  );
}
