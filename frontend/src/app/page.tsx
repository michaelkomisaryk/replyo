import { BackendStatus } from "@/components/BackendStatus";

export default function Home() {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold">Welcome to Replyo</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
          This is the initial frontend shell for the MicroCRM MVP. The layout
          includes a header and sidebar placeholder while API integration is
          wired to the Django backend.
        </p>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold">Backend status</h3>
        <div className="mt-4">
          <BackendStatus />
        </div>
      </section>
    </div>
  );
}
