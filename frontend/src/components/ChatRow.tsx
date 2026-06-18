import Link from "next/link";

import type { Chat } from "@/lib/api";
import {
  chatDisplayName,
  formatWaitTime,
  urgencyClasses,
} from "@/lib/chat-utils";

type ChatRowProps = {
  chat: Chat;
};

export function ChatRow({ chat }: ChatRowProps) {
  const waitLabel = formatWaitTime(chat.wait_seconds);
  const showWaitTime = chat.priority === "waiting_reply" && waitLabel;

  return (
    <Link
      href={`/chats/${chat.id}`}
      className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-zinc-50"
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-medium text-zinc-900">
            {chatDisplayName(chat)}
          </p>
          {chat.is_pinned && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-700">
              Pinned
            </span>
          )}
          {chat.has_new_message_badge && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
              New message
            </span>
          )}
        </div>
        <p className="truncate text-xs text-zinc-500">
          @{chat.client_username}
          {chat.assigned_to_email ? ` · ${chat.assigned_to_email}` : " · Unassigned"}
        </p>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-1">
        {showWaitTime ? (
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${urgencyClasses(chat.wait_urgency)}`}
          >
            Waiting {waitLabel}
          </span>
        ) : (
          <span className="text-xs text-zinc-400">{chat.priority_label}</span>
        )}
      </div>
    </Link>
  );
}
