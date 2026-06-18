"use client";

import { useSession } from "next-auth/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  createChatOrder,
  fetchChatOrders,
  updateOrderStatus,
  type Order,
} from "@/lib/api";

const ORDER_STATUSES = [
  { value: "new_client", label: "New Client" },
  { value: "waiting_payment", label: "Waiting Payment" },
  { value: "paid", label: "Paid" },
  { value: "sent", label: "Sent" },
  { value: "completed", label: "Completed" },
  { value: "rejected", label: "Rejected" },
] as const;

const PRIORITY_LABELS: Record<string, string> = {
  new_clients: "New Clients",
  waiting_reply: "Waiting for Reply",
  active_orders: "Active Orders",
  completed_orders: "Completed Orders",
  rejected: "Rejected Clients",
};

type OrderStatusPanelProps = {
  accessToken: string;
  chatId: number;
  chatPriority?: string;
};

export function OrderStatusPanel({
  accessToken,
  chatId,
  chatPriority,
}: OrderStatusPanelProps) {
  const { data: session } = useSession();
  const canManage = ["admin", "manager"].includes(session?.user?.role ?? "");
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { data: orders, isLoading } = useQuery({
    queryKey: ["chat-orders", chatId, accessToken],
    queryFn: () => fetchChatOrders(accessToken, chatId),
    enabled: Boolean(accessToken),
  });

  const activeOrder =
    orders?.find(
      (order) => !["completed", "rejected"].includes(order.status),
    ) ?? null;

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["chat-orders", chatId] });
    await queryClient.invalidateQueries({ queryKey: ["client-card"] });
    await queryClient.invalidateQueries({ queryKey: ["chat", chatId] });
    await queryClient.invalidateQueries({ queryKey: ["chats"] });
  }

  async function handleCreateOrder() {
    setLoading(true);
    setError("");
    try {
      await createChatOrder(accessToken, chatId, "waiting_payment");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create order.");
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(order: Order, status: string) {
    setLoading(true);
    setError("");
    try {
      await updateOrderStatus(accessToken, order.id, status);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update status.");
    } finally {
      setLoading(false);
    }
  }

  if (isLoading) {
    return (
      <section className="border-b border-zinc-200 bg-zinc-50 px-5 py-3">
        <p className="text-xs text-zinc-500">Loading order status...</p>
      </section>
    );
  }

  return (
    <section className="border-b border-zinc-200 bg-zinc-50 px-5 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Order status
          </p>
          {chatPriority && (
            <p className="mt-1 text-xs text-zinc-600">
              Chat priority: {PRIORITY_LABELS[chatPriority] ?? chatPriority}
            </p>
          )}
        </div>

        {canManage && !activeOrder && (
          <button
            type="button"
            onClick={handleCreateOrder}
            disabled={loading}
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60"
          >
            {loading ? "Creating..." : "Create order"}
          </button>
        )}
      </div>

      {activeOrder ? (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-zinc-900">
            Order #{activeOrder.id}
          </span>
          {canManage ? (
            <select
              value={activeOrder.status}
              disabled={loading}
              onChange={(event) =>
                handleStatusChange(activeOrder, event.target.value)
              }
              className="rounded-lg border border-zinc-300 bg-white px-2 py-1 text-sm outline-none focus:border-zinc-500"
            >
              {ORDER_STATUSES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <span className="rounded-full bg-white px-2 py-0.5 text-xs text-zinc-700 ring-1 ring-zinc-200">
              {activeOrder.status_label}
            </span>
          )}
        </div>
      ) : (
        <p className="mt-2 text-sm text-zinc-600">No active order for this chat.</p>
      )}

      {error && <p className="mt-2 text-xs text-red-700">{error}</p>}
    </section>
  );
}
