"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchChats } from "@/lib/api";

export function ChatList() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;

  const { data, isLoading, error } = useQuery({
    queryKey: ["chats", accessToken],
    queryFn: () => fetchChats(accessToken!),
    enabled: Boolean(accessToken),
  });

  if (!accessToken || isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading chats...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-red-700">Could not load chats.</p>
      </section>
    );
  }

  if (!data?.length) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold">No chats yet</h3>
        <p className="mt-2 text-sm text-zinc-600">
          Incoming Instagram DMs will appear here after your webhook receives
          messages.
        </p>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <ul className="divide-y divide-zinc-100">
        {data.map((chat) => (
          <li key={chat.id}>
            <Link
              href={`/chats/${chat.id}`}
              className="flex items-center justify-between px-5 py-4 transition hover:bg-zinc-50"
            >
              <div>
                <p className="text-sm font-medium text-zinc-900">
                  {chat.client_display_name || `@${chat.client_username}`}
                </p>
                <p className="text-xs text-zinc-500">@{chat.client_username}</p>
              </div>
              <span className="text-xs text-zinc-400">Open</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
