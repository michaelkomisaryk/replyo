const ACTIVE_STATUSES = new Set([
  "new_client",
  "waiting_payment",
  "paid",
  "sent",
]);

export function orderStatusClasses(status: string): string {
  switch (status) {
    case "completed":
      return "bg-emerald-100 text-emerald-800 ring-emerald-200";
    case "rejected":
      return "bg-red-100 text-red-800 ring-red-200";
    case "paid":
    case "sent":
      return "bg-blue-100 text-blue-800 ring-blue-200";
    case "waiting_payment":
      return "bg-amber-100 text-amber-800 ring-amber-200";
    default:
      return "bg-zinc-100 text-zinc-700 ring-zinc-200";
  }
}

export function isActiveOrderStatus(status: string): boolean {
  return ACTIVE_STATUSES.has(status);
}

export function formatOrderDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function clientLabel(order: {
  client_display_name: string;
  client_username: string;
}): string {
  return order.client_display_name || `@${order.client_username}`;
}
