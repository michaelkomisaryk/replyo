"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchChatPriorities, fetchChats, type Chat } from "@/lib/api";
import { PRIORITY_SECTION_ORDER } from "@/lib/chat-utils";

import { AssigneeFilter, type AssigneeFilterValue } from "@/components/AssigneeFilter";

import { ChatRow } from "@/components/ChatRow";
import { ChatDashboardSkeleton } from "@/components/ChatListSkeleton";

type DashboardFilter = "all" | "active_orders" | "archived" | "rejected";

const FILTER_TABS: { id: DashboardFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "active_orders", label: "Active orders" },
  { id: "archived", label: "Archived" },
  { id: "rejected", label: "Rejected" },
];

const EMPTY_MESSAGES: Record<DashboardFilter, { title: string; body: string }> = {
  all: {
    title: "No active chats",
    body: "Incoming Instagram DMs will appear here once your webhook receives messages.",
  },
  active_orders: {
    title: "No active orders",
    body: "Chats with orders in progress will show up in this filter.",
  },
  archived: {
    title: "No archived chats",
    body: "Completed or inactive conversations are archived automatically after 24 hours.",
  },
  rejected: {
    title: "No rejected clients",
    body: "Clients marked as rejected will appear here for reference.",
  },
};

function FilterTabs({
  active,
  onChange,
}: {
  active: DashboardFilter;
  onChange: (filter: DashboardFilter) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTER_TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`rounded-full px-4 py-2 text-sm font-medium transition ${
            active === tab.id
              ? "bg-zinc-900 text-white"
              : "bg-white text-zinc-700 ring-1 ring-zinc-200 hover:bg-zinc-50"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function EmptyState({ filter }: { filter: DashboardFilter }) {
  const copy = EMPTY_MESSAGES[filter];
  return (
    <section className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center shadow-sm">
      <h3 className="text-base font-semibold text-zinc-900">{copy.title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-zinc-600">{copy.body}</p>
    </section>
  );
}

function FlatChatList({ chats }: { chats: Chat[] }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <ul className="divide-y divide-zinc-100">
        {chats.map((chat) => (
          <li key={chat.id}>
            <ChatRow chat={chat} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function PriorityBucketsView({
  buckets,
}: {
  buckets: Awaited<ReturnType<typeof fetchChatPriorities>>["buckets"];
}) {
  const byPriority = new Map(buckets.map((bucket) => [bucket.priority, bucket]));
  const orderedBuckets = PRIORITY_SECTION_ORDER.map((priority) => {
    const bucket = byPriority.get(priority);
    return (
      bucket ?? {
        priority,
        label: priority.replaceAll("_", " "),
        count: 0,
        chats: [],
      }
    );
  });

  const totalChats = orderedBuckets.reduce((sum, bucket) => sum + bucket.count, 0);
  if (totalChats === 0) {
    return <EmptyState filter="all" />;
  }

  return (
    <div className="space-y-6">
      {orderedBuckets.map((bucket) => {
        const isTopSection =
          bucket.priority === "new_clients" || bucket.priority === "waiting_reply";

        return (
          <section
            key={bucket.priority}
            className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm"
          >
            <header
              className={`flex items-center justify-between border-b border-zinc-100 px-5 py-3 ${
                isTopSection ? "bg-zinc-50" : "bg-white"
              }`}
            >
              <div>
                <h3 className="text-sm font-semibold text-zinc-900">{bucket.label}</h3>
                {isTopSection && (
                  <p className="text-xs text-zinc-500">
                    {bucket.priority === "new_clients"
                      ? "First-time messages needing a reply"
                      : "Clients waiting longer than the reply threshold"}
                  </p>
                )}
              </div>
              <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600">
                {bucket.count}
              </span>
            </header>

            {bucket.count === 0 ? (
              <p className="px-5 py-4 text-sm text-zinc-500">No chats in this section.</p>
            ) : (
              <ul className="divide-y divide-zinc-100">
                {bucket.chats.map((chat) => (
                  <li key={chat.id}>
                    <ChatRow chat={chat} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </div>
  );
}

function FilteredChatList({
  filter,
  assignedTo,
}: {
  filter: Exclude<DashboardFilter, "all">;
  assignedTo: AssigneeFilterValue;
}) {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;

  const { data, isLoading, error } = useQuery({
    queryKey: ["chats", filter, assignedTo, accessToken],
    queryFn: () => {
      const assignee = assignedTo || undefined;
      if (filter === "active_orders") {
        return fetchChats(accessToken!, {
          view: "active",
          priority: "active_orders",
          assignedTo: assignee,
        });
      }
      if (filter === "archived") {
        return fetchChats(accessToken!, { view: "archived", assignedTo: assignee });
      }
      return fetchChats(accessToken!, { view: "rejected", assignedTo: assignee });
    },
    enabled: Boolean(accessToken),
  });

  if (!accessToken || isLoading) {
    return <ChatDashboardSkeleton />;
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-6 shadow-sm">
        <p className="text-sm text-red-700">Could not load chats.</p>
      </section>
    );
  }

  if (!data?.length) {
    return <EmptyState filter={filter} />;
  }

  return <FlatChatList chats={data} />;
}

export function ChatDashboard() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const [filter, setFilter] = useState<DashboardFilter>("all");
  const [assignedTo, setAssignedTo] = useState<AssigneeFilterValue>("");

  const {
    data: priorities,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["chat-priorities", assignedTo, accessToken],
    queryFn: () =>
      fetchChatPriorities(accessToken!, {
        assignedTo: assignedTo || undefined,
      }),
    enabled: Boolean(accessToken) && filter === "all",
  });

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <FilterTabs active={filter} onChange={setFilter} />
        <AssigneeFilter value={assignedTo} onChange={setAssignedTo} />
      </div>

      {filter === "all" ? (
        !accessToken || isLoading ? (
          <ChatDashboardSkeleton />
        ) : error ? (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-6 shadow-sm">
            <p className="text-sm text-red-700">Could not load chat priorities.</p>
          </section>
        ) : (
          <PriorityBucketsView buckets={priorities?.buckets ?? []} />
        )
      ) : (
        <FilteredChatList filter={filter} assignedTo={assignedTo} />
      )}
    </div>
  );
}
