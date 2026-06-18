"use client";

import { FormEvent, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchClientCard, updateClientNotes } from "@/lib/api";

type ClientCardPanelProps = {
  accessToken: string;
  clientId: number;
};

function formatDate(value: string) {
  return new Date(value).toLocaleDateString();
}

export function ClientCardPanel({ accessToken, clientId }: ClientCardPanelProps) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [saveError, setSaveError] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["client-card", clientId, accessToken],
    queryFn: () => fetchClientCard(accessToken, clientId),
    enabled: Boolean(accessToken),
  });

  useEffect(() => {
    if (data) {
      setNotes(data.notes);
    }
  }, [data]);

  async function handleSaveNotes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data?.can_edit) {
      return;
    }

    setSaving(true);
    setSaveMessage("");
    setSaveError("");

    try {
      await updateClientNotes(accessToken, clientId, notes);
      setSaveMessage("Notes saved.");
      await queryClient.invalidateQueries({ queryKey: ["client-card", clientId] });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save notes.");
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) {
    return (
      <aside className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-zinc-600">Loading client card...</p>
      </aside>
    );
  }

  if (error || !data) {
    return (
      <aside className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-red-700">Could not load client card.</p>
      </aside>
    );
  }

  return (
    <aside className="flex h-full flex-col rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <div className="border-b border-zinc-200 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Client card
        </h3>
        <p className="mt-2 text-base font-semibold text-zinc-900">
          {data.display_name || `@${data.instagram_username}`}
        </p>
        <p className="text-sm text-zinc-600">@{data.instagram_username}</p>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Notes
          </h4>
          {data.can_edit ? (
            <form onSubmit={handleSaveNotes} className="mt-2 space-y-2">
              <textarea
                rows={4}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="w-full resize-none rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                placeholder="Add notes about this client..."
              />
              {saveError && (
                <p className="text-xs text-red-700">{saveError}</p>
              )}
              {saveMessage && (
                <p className="text-xs text-emerald-700">{saveMessage}</p>
              )}
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60"
              >
                {saving ? "Saving..." : "Save notes"}
              </button>
            </form>
          ) : (
            <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-700">
              {data.notes || "No notes yet."}
            </p>
          )}
        </section>

        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Order history
          </h4>
          {data.orders.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-500">No orders yet.</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {data.orders.map((order) => (
                <li
                  key={order.id}
                  className="rounded-lg border border-zinc-100 px-3 py-2 text-sm"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-zinc-900">
                      Order #{order.id}
                    </span>
                    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
                      {order.status_label}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    {formatDate(order.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </aside>
  );
}
