import { BackendStatus } from "@/components/BackendStatus";
import { DashboardWelcome } from "@/components/DashboardWelcome";

export default function Home() {
  return (
    <div className="space-y-6">
      <DashboardWelcome />

      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold">Backend status</h3>
        <div className="mt-4">
          <BackendStatus />
        </div>
      </section>
    </div>
  );
}
