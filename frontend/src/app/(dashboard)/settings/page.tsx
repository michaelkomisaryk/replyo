import { Suspense } from "react";

import { InstagramSettings } from "@/components/InstagramSettings";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Manage shop integrations and connection status.
        </p>
      </div>

      <Suspense
        fallback={
          <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-zinc-600">Loading settings...</p>
          </section>
        }
      >
        <InstagramSettings />
      </Suspense>
    </div>
  );
}
