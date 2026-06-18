"use client";

import { useSession } from "next-auth/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  archiveChat,
  assignChat,
  escalateChat,
  fetchTeamMembers,
  pinChat,
  type Chat,
} from "@/lib/api";
import { formatWaitTime, urgencyClasses } from "@/lib/chat-utils";

const PRIORITY_LABELS: Record<string, string> = {
  new_clients: "New Clients",
  waiting_reply: "Waiting for Reply",
  active_orders: "Active Orders",
  completed_orders: "Completed Orders",
  rejected: "Rejected Clients",
};

type ChatControlsProps = {
  accessToken: string;
  chat: Chat;
  onUpdated: () => void;
};

export function ChatControls({ accessToken, chat, onUpdated }: ChatControlsProps) {
  const { data: session } = useSession();
  const role = session?.user?.role ?? "";
  const canManage = ["admin", "manager"].includes(role);
  const isSupport = role === "support_manager";
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { data: teamMembers } = useQuery({
    queryKey: ["team-members", accessToken],
    queryFn: () => fetchTeamMembers(accessToken),
    enabled: Boolean(accessToken) && canManage,
  });

  async function runAction(action: () => Promise<unknown>) {
    setLoading(true);
    setError("");
    try {
      await action();
      onUpdated();
      await queryClient.invalidateQueries({ queryKey: ["chat", chat.id] });
      await queryClient.invalidateQueries({ queryKey: ["chats"] });
      await queryClient.invalidateQueries({ queryKey: ["chat-priorities"] });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setLoading(false);
    }
  }

  const waitLabel = formatWaitTime(chat.wait_seconds);

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <div className="border-b border-zinc-200 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Chat controls
        </h3>
      </div>

      <div className="space-y-4 p-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Priority
          </p>
          <p className="mt-1 text-sm font-medium text-zinc-900">
            {PRIORITY_LABELS[chat.priority] ?? chat.priority_label}
          </p>
          {chat.priority === "waiting_reply" && waitLabel && (
            <span
              className={`mt-2 inline-block rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${urgencyClasses(chat.wait_urgency)}`}
            >
              Waiting {waitLabel}
            </span>
          )}
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Assigned to
          </p>
          {canManage ? (
            <select
              value={chat.assigned_to ?? ""}
              disabled={loading}
              onChange={(event) => {
                const value = event.target.value;
                void runAction(() =>
                  assignChat(
                    accessToken,
                    chat.id,
                    value ? Number(value) : null,
                  ),
                );
              }}
              className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-zinc-500"
            >
              <option value="">Unassigned</option>
              {teamMembers?.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.email} ({member.role})
                </option>
              ))}
            </select>
          ) : (
            <p className="mt-1 text-sm text-zinc-700">
              {chat.assigned_to_email ?? "Unassigned"}
            </p>
          )}
        </div>

        {canManage && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() =>
                void runAction(() =>
                  pinChat(accessToken, chat.id, !chat.is_pinned),
                )
              }
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-60"
            >
              {chat.is_pinned ? "Unpin" : "Pin chat"}
            </button>
            {!chat.is_archived && (
              <button
                type="button"
                disabled={loading}
                onClick={() => void runAction(() => archiveChat(accessToken, chat.id))}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:opacity-60"
              >
                Archive
              </button>
            )}
          </div>
        )}

        {isSupport && chat.assigned_to && (
          <button
            type="button"
            disabled={loading}
            onClick={() => void runAction(() => escalateChat(accessToken, chat.id))}
            className="w-full rounded-lg bg-amber-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-amber-700 disabled:opacity-60"
          >
            Escalate to team
          </button>
        )}

        {error && <p className="text-xs text-red-700">{error}</p>}
      </div>
    </section>
  );
}
