"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchChats, fetchClients } from "@/lib/api";

export function ClientList() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;

  const clientsQuery = useQuery({
    queryKey: ["clients", accessToken],
    queryFn: () => fetchClients(accessToken!),
    enabled: Boolean(accessToken),
  });

  const chatsQuery = useQuery({
    queryKey: ["chats", "all", accessToken],
    queryFn: () => fetchChats(accessToken!, { view: "all" }),
    enabled: Boolean(accessToken),
  });

  if (!accessToken || clientsQuery.isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading clients...</p>
      </section>
    );
  }

  if (clientsQuery.error) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-red-700">Could not load clients.</p>
      </section>
    );
  }

  const clients = clientsQuery.data ?? [];
  const chatByClientId = new Map(
    (chatsQuery.data ?? []).map((chat) => [chat.client, chat.id]),
  );

  if (clients.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center shadow-sm">
        <h3 className="text-base font-semibold">No clients yet</h3>
        <p className="mt-2 text-sm text-zinc-600">
          Clients appear when Instagram messages are received. Connect Instagram
          in{" "}
          <Link href="/settings" className="underline">
            Settings
          </Link>{" "}
          first.
        </p>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <ul className="divide-y divide-zinc-100">
        {clients.map((client) => {
          const chatId = chatByClientId.get(client.id);
          const label = client.display_name || `@${client.instagram_username}`;

          return (
            <li key={client.id} className="flex items-center justify-between gap-4 px-5 py-4">
              <div>
                <p className="text-sm font-medium text-zinc-900">{label}</p>
                <p className="text-xs text-zinc-500">@{client.instagram_username}</p>
              </div>
              {chatId ? (
                <Link
                  href={`/chats/${chatId}`}
                  className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700"
                >
                  Open chat
                </Link>
              ) : (
                <span className="text-xs text-zinc-400">No chat</span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
