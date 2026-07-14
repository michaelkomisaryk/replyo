import { OrderList } from "@/components/OrderList";

export default function OrdersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Orders</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Track order status across all clients. Open a chat to update status or
          create a new order.
        </p>
      </div>
      <OrderList />
    </div>
  );
}
