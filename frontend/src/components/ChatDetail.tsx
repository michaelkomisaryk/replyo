"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatControls } from "@/components/ChatControls";
import { ChatDetailSkeleton } from "@/components/ChatDetailSkeleton";
import { ClientCardPanel } from "@/components/ClientCardPanel";
import { MessageThread } from "@/components/MessageThread";
import { OrderStatusPanel } from "@/components/OrderStatusPanel";
import { ReplyComposer } from "@/components/ReplyComposer";
import { fetchChat, fetchMessages } from "@/lib/api";

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
    refetchInterval: 10000,
  });

  const messagesQuery = useQuery({
    queryKey: ["messages", chatId, accessToken],
    queryFn: () => fetchMessages(accessToken!, chatId),
    enabled: Boolean(accessToken),
    refetchInterval: 5000,
  });

  function refreshChatData() {
    void queryClient.invalidateQueries({ queryKey: ["messages", chatId] });
    void queryClient.invalidateQueries({ queryKey: ["chat", chatId] });
    void queryClient.invalidateQueries({ queryKey: ["chats"] });
    void queryClient.invalidateQueries({ queryKey: ["chat-priorities"] });
    void queryClient.invalidateQueries({ queryKey: ["chat-orders", chatId] });
    void queryClient.invalidateQueries({ queryKey: ["client-card"] });
  }

  if (!accessToken || chatQuery.isLoading || messagesQuery.isLoading) {
    return <ChatDetailSkeleton />;
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
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold">
              {chat.client_display_name || `@${chat.client_username}`}
            </h3>
            {chat.has_new_message_badge && (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
                New message
              </span>
            )}
            {chat.is_pinned && (
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-700">
                Pinned
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-500">@{chat.client_username}</p>
        </div>

        <MessageThread
          messages={messages}
          isRefreshing={messagesQuery.isFetching && !messagesQuery.isLoading}
        />

        <ReplyComposer
          accessToken={accessToken}
          chatId={chatId}
          onSent={refreshChatData}
        />
      </div>

      <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto">
        <ChatControls
          accessToken={accessToken}
          chat={chat}
          onUpdated={refreshChatData}
        />
        <OrderStatusPanel
          accessToken={accessToken}
          chatId={chatId}
          chatPriority={chat.priority}
        />
        <ClientCardPanel accessToken={accessToken} clientId={chat.client} />
      </aside>
    </div>
  );
}
