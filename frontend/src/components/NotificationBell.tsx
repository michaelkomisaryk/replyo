"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type ChatNotification,
} from "@/lib/api";

function NotificationItem({
  notification,
  onDismiss,
}: {
  notification: ChatNotification;
  onDismiss: (id: number) => void;
}) {
  const content = (
    <div className="px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {notification.kind_label}
      </p>
      <p className="mt-1 text-sm text-zinc-900">{notification.message}</p>
      <p className="mt-1 text-xs text-zinc-400">
        {new Date(notification.created_at).toLocaleString()}
      </p>
    </div>
  );

  if (notification.chat_id) {
    return (
      <div className="flex items-start justify-between gap-2 hover:bg-zinc-50">
        <Link
          href={`/chats/${notification.chat_id}`}
          className="min-w-0 flex-1"
          onClick={() => onDismiss(notification.id)}
        >
          {content}
        </Link>
        <button
          type="button"
          onClick={() => onDismiss(notification.id)}
          className="px-3 py-3 text-xs text-zinc-500 hover:text-zinc-800"
        >
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between gap-2">
      <div className="min-w-0 flex-1">{content}</div>
      <button
        type="button"
        onClick={() => onDismiss(notification.id)}
        className="px-3 py-3 text-xs text-zinc-500 hover:text-zinc-800"
      >
        Dismiss
      </button>
    </div>
  );
}

export function NotificationBell() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", accessToken],
    queryFn: () => fetchNotifications(accessToken!),
    enabled: Boolean(accessToken),
    refetchInterval: 30000,
  });

  const dismissMutation = useMutation({
    mutationFn: (notificationId: number) =>
      markNotificationRead(accessToken!, notificationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const dismissAllMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(accessToken!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = data?.unread_count ?? 0;
  const notifications = data?.results ?? [];

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="relative rounded-full border border-zinc-300 p-2 text-zinc-700 transition hover:bg-zinc-50"
        aria-label="Notifications"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          className="h-4 w-4"
        >
          <path d="M15 17H9c-2.2 0-4-1.8-4-4V9.5C5 6.5 7.5 4 10.5 4c.3-1.2 1.4-2 2.6-2s2.3.8 2.6 2C18.7 4 21 6.5 21 9.5V13c0 2.2-1.8 4-4 4Z" />
          <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-[calc(100%+0.5rem)] z-50 w-96 overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-zinc-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => dismissAllMutation.mutate()}
                className="text-xs text-zinc-500 hover:text-zinc-800"
              >
                Mark all read
              </button>
            )}
          </div>

          {isLoading ? (
            <p className="px-4 py-6 text-sm text-zinc-500">Loading...</p>
          ) : notifications.length === 0 ? (
            <p className="px-4 py-6 text-sm text-zinc-500">No notifications yet.</p>
          ) : (
            <ul className="max-h-96 divide-y divide-zinc-100 overflow-y-auto">
              {notifications.map((notification) => (
                <li
                  key={notification.id}
                  className={notification.is_read ? "opacity-70" : "bg-zinc-50"}
                >
                  <NotificationItem
                    notification={notification}
                    onDismiss={(id) => dismissMutation.mutate(id)}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
