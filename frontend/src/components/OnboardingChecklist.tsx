"use client";

import { useSession } from "next-auth/react";
import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchOnboarding, inviteTeamMember } from "@/lib/api";
import { InstagramSettingsLink } from "@/components/InstagramSettings";

export function OnboardingChecklist() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const isAdmin = session?.user?.role === "admin";
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"manager" | "support_manager">("manager");
  const [inviteError, setInviteError] = useState("");
  const [inviteSuccess, setInviteSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["onboarding", accessToken],
    queryFn: () => fetchOnboarding(accessToken!),
    enabled: Boolean(accessToken),
  });

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setInviteError("");
    setInviteSuccess("");
    setLoading(true);

    try {
      const result = await inviteTeamMember(accessToken, { email, role });
      setInviteSuccess(`Invitation sent to ${result.email}.`);
      setEmail("");
      await queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Invite failed.");
    } finally {
      setLoading(false);
    }
  }

  if (!accessToken || isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading onboarding checklist...</p>
      </section>
    );
  }

  if (error || !data) {
    return null;
  }

  if (data.is_complete) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold">Getting started</h3>
          <p className="mt-1 text-sm text-zinc-600">
            Complete these steps to set up your shop.
          </p>
        </div>
        <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700">
          {data.completed_count}/{data.total_count} done
        </span>
      </div>

      <ul className="mt-5 space-y-3">
        {data.steps.map((step) => (
          <li
            key={step.id}
            className="flex items-start gap-3 rounded-lg border border-zinc-100 px-3 py-3"
          >
            <span
              className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold ${
                step.completed
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-zinc-100 text-zinc-500"
              }`}
            >
              {step.completed ? "✓" : "•"}
            </span>
            <div>
              <p className="text-sm font-medium text-zinc-900">{step.label}</p>
              {step.id === "instagram_connected" &&
                !step.completed &&
                isAdmin && (
                  <p className="mt-1 text-xs text-zinc-500">
                    <InstagramSettingsLink />
                  </p>
                )}
            </div>
          </li>
        ))}
      </ul>

      {isAdmin && !data.steps.find((step) => step.id === "team_invited")?.completed && (
        <form onSubmit={handleInvite} className="mt-6 space-y-3 border-t border-zinc-100 pt-5">
          <h4 className="text-sm font-semibold text-zinc-900">Invite a team member</h4>
          <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto]">
            <input
              type="email"
              required
              placeholder="teammate@shop.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
            />
            <select
              value={role}
              onChange={(event) =>
                setRole(event.target.value as "manager" | "support_manager")
              }
              className="rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
            >
              <option value="manager">Manager</option>
              <option value="support_manager">Support Manager</option>
            </select>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60"
            >
              {loading ? "Sending..." : "Send invite"}
            </button>
          </div>
          {inviteError && (
            <p className="text-sm text-red-700">{inviteError}</p>
          )}
          {inviteSuccess && (
            <p className="text-sm text-emerald-700">{inviteSuccess}</p>
          )}
        </form>
      )}
    </section>
  );
}
