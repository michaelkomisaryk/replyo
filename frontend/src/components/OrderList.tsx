"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchOrders, type Order } from "@/lib/api";
import {
  clientLabel,
  formatOrderDate,
  isActiveOrderStatus,
  orderStatusClasses,
} from "@/lib/order-utils";

type OrderFilter = "all" | "active" | "completed" | "rejected";

const FILTER_TABS: { id: OrderFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "active", label: "Active" },
  { id: "completed", label: "Completed" },
  { id: "rejected", label: "Rejected" },
];

function filterOrders(orders: Order[], filter: OrderFilter): Order[] {
  if (filter === "all") {
    return orders;
  }
  if (filter === "active") {
    return orders.filter((order) => isActiveOrderStatus(order.status));
  }
  if (filter === "completed") {
    return orders.filter((order) => order.status === "completed");
  }
  return orders.filter((order) => order.status === "rejected");
}

export function OrderList() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const [filter, setFilter] = useState<OrderFilter>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", accessToken],
    queryFn: () => fetchOrders(accessToken!),
    enabled: Boolean(accessToken),
  });

  const orders = useMemo(
    () => filterOrders(data ?? [], filter),
    [data, filter],
  );

  if (!accessToken || isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading orders...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-red-700">Could not load orders.</p>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setFilter(tab.id)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              filter === tab.id
                ? "bg-zinc-900 text-white"
                : "bg-white text-zinc-700 ring-1 ring-zinc-200 hover:bg-zinc-50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {orders.length === 0 ? (
        <section className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center shadow-sm">
          <h3 className="text-base font-semibold">No orders found</h3>
          <p className="mt-2 text-sm text-zinc-600">
            {filter === "all"
              ? "Create an order from a chat to start tracking fulfillment."
              : "No orders match this filter."}
          </p>
          {filter === "all" && (
            <Link
              href="/chats"
              className="mt-4 inline-block text-sm font-medium underline"
            >
              Go to chats
            </Link>
          )}
        </section>
      ) : (
        <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
          <ul className="divide-y divide-zinc-100">
            {orders.map((order) => (
              <li
                key={order.id}
                className="flex flex-wrap items-center justify-between gap-4 px-5 py-4"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium text-zinc-900">
                      Order #{order.id}
                    </p>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${orderStatusClasses(order.status)}`}
                    >
                      {order.status_label}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-700">
                    {clientLabel(order)}
                  </p>
                  <p className="text-xs text-zinc-500">
                    @{order.client_username} · {formatOrderDate(order.created_at)}
                  </p>
                </div>

                {order.chat ? (
                  <Link
                    href={`/chats/${order.chat}`}
                    className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700"
                  >
                    Open chat
                  </Link>
                ) : (
                  <span className="text-xs text-zinc-400">No linked chat</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
