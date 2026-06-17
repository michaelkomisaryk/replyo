"use client";

import { useQuery } from "@tanstack/react-query";

import { API_BASE_URL, fetchHealth } from "@/lib/api";

export function BackendStatus() {
  const { data, error, isLoading, isSuccess } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  if (isLoading) {
    return (
      <p className="text-sm text-zinc-600">Checking backend connection...</p>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        <p className="font-medium">Backend unreachable</p>
        <p className="mt-1">
          Could not reach <code>{API_BASE_URL}/api/health/</code>. Start the
          Django server and try again.
        </p>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
        <p className="font-medium">Backend connected</p>
        <p className="mt-1">
          Health check returned <code>{JSON.stringify(data)}</code>
        </p>
      </div>
    );
  }

  return null;
}
