import type { Chat } from "@/lib/api";

export type WaitUrgency = "yellow" | "orange" | "red";

export function formatWaitTime(seconds: number | null | undefined): string | null {
  if (seconds == null || seconds < 0) {
    return null;
  }

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0 && minutes > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (hours > 0) {
    return `${hours}h`;
  }
  if (minutes > 0) {
    return `${minutes}m`;
  }
  return "<1m";
}

export function urgencyClasses(urgency: WaitUrgency | null | undefined): string {
  switch (urgency) {
    case "red":
      return "bg-red-100 text-red-800 ring-red-200";
    case "orange":
      return "bg-orange-100 text-orange-800 ring-orange-200";
    case "yellow":
      return "bg-amber-100 text-amber-800 ring-amber-200";
    default:
      return "bg-zinc-100 text-zinc-600 ring-zinc-200";
  }
}

export function chatDisplayName(chat: Chat): string {
  return chat.client_display_name || `@${chat.client_username}`;
}

export const PRIORITY_SECTION_ORDER = [
  "new_clients",
  "waiting_reply",
  "active_orders",
  "completed_orders",
] as const;
