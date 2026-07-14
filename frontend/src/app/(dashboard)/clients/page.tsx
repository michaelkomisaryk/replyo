import { ClientList } from "@/components/ClientList";

export default function ClientsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Clients</h1>
        <p className="mt-1 text-sm text-zinc-600">
          All clients synced from Instagram. Use the search bar in the header to
          find someone quickly.
        </p>
      </div>
      <ClientList />
    </div>
  );
}
