"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ClientCardPanel } from "@/components/ClientCardPanel";
import { OrderStatusPanel } from "@/components/OrderStatusPanel";
import { ReplyComposer } from "@/components/ReplyComposer";
import { fetchChat, fetchMessages } from "@/lib/api";

function formatTime(value: string) {
  return new Date(value).toLocaleString();
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

type ChatDetailProps = {
  chatId: number;
};

export function ChatDetail({ chatId }: ChatDetailProps) {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const queryClient = useQueryClient();

  const chatQuery = useQuery({
    queryKey: ["chat", chatId, accessToken],
    queryFn: () => fetchChat(accessToken!, chatId),
    enabled: Boolean(accessToken),
  });

  const messagesQuery = useQuery({
    queryKey: ["messages", chatId, accessToken],
    queryFn: () => fetchMessages(accessToken!, chatId),
    enabled: Boolean(accessToken),
    refetchInterval: 5000,
  });

  function refreshMessages() {
    void queryClient.invalidateQueries({ queryKey: ["messages", chatId] });
    void queryClient.invalidateQueries({ queryKey: ["chats"] });
  }

  if (!accessToken || chatQuery.isLoading || messagesQuery.isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading conversation...</p>
      </section>
    );
  }

  if (chatQuery.error || !chatQuery.data) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-red-700">Chat not found.</p>
        <Link href="/chats" className="mt-3 inline-block text-sm underline">
          Back to chats
        </Link>
      </section>
    );
  }

  const chat = chatQuery.data;
  const messages = messagesQuery.data ?? [];

  return (
    <div className="grid h-[calc(100vh-8rem)] gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <Link href="/chats" className="text-xs text-zinc-500 underline">
            Back to chats
          </Link>
          <h3 className="mt-1 text-base font-semibold">
            {chat.client_display_name || `@${chat.client_username}`}
          </h3>
          <p className="text-sm text-zinc-500">@{chat.client_username}</p>
        </div>

        <OrderStatusPanel
          accessToken={accessToken}
          chatId={chatId}
          chatPriority={chat.priority}
        />

        <div className="flex-1 space-y-3 overflow-y-auto p-5">
          {messages.length === 0 ? (
            <p className="text-sm text-zinc-500">No messages yet.</p>
          ) : (
            messages.map((message) => {
              const isOutbound = message.direction === "outbound";
              return (
                <div
                  key={message.id}
                  className={`flex ${isOutbound ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                      isOutbound
                        ? "bg-zinc-900 text-white"
                        : "bg-zinc-100 text-zinc-900"
                    }`}
                  >
                    <p>{message.content}</p>
                    <div
                      className={`mt-1 text-[11px] ${
                        isOutbound ? "text-zinc-300" : "text-zinc-500"
                      }`}
                    >
                      {formatTime(message.sent_at)}
                      {isOutbound && message.delivery_status && (
                        <>
                          {" "}
                          · {deliveryLabel(
                            message.delivery_status,
                            message.delivery_error,
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <ReplyComposer
          accessToken={accessToken}
          chatId={chatId}
          onSent={refreshMessages}
        />
      </div>

      <ClientCardPanel accessToken={accessToken} clientId={chat.client} />
    </div>
  );
}
