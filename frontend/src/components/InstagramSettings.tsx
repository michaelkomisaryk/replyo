"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  disconnectInstagram,
  fetchInstagramConnectUrl,
  fetchInstagramStatus,
  mockConnectInstagram,
  refreshInstagramToken,
} from "@/lib/api";

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}

export function InstagramSettings() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const isAdmin = session?.user?.role === "admin";
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();

  const [actionError, setActionError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["instagram-status", accessToken],
    queryFn: () => fetchInstagramStatus(accessToken!),
    enabled: Boolean(accessToken),
  });

  useEffect(() => {
    const instagram = searchParams.get("instagram");
    const message = searchParams.get("message");
    if (instagram === "connected") {
      setActionMessage("Instagram account connected successfully.");
      void queryClient.invalidateQueries({ queryKey: ["instagram-status"] });
      void queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    } else if (instagram === "error") {
      setActionError(message ?? "Instagram connection failed.");
    }
  }, [searchParams, queryClient]);

  async function handleConnect() {
    if (!accessToken) {
      return;
    }

    setActionError("");
    setActionMessage("");
    setLoadingAction("connect");

    try {
      const result = await fetchInstagramConnectUrl(accessToken);
      if (result.authorization_url) {
        window.location.href = result.authorization_url;
        return;
      }

      if (result.mock_available) {
        const status = await mockConnectInstagram(accessToken);
        setActionMessage(`Connected @${status.username} (development mock).`);
        await queryClient.invalidateQueries({ queryKey: ["instagram-status"] });
        await queryClient.invalidateQueries({ queryKey: ["onboarding"] });
        return;
      }

      setActionError(result.detail ?? "Instagram OAuth is not configured.");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Connect failed.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleDisconnect() {
    if (!accessToken) {
      return;
    }

    setActionError("");
    setActionMessage("");
    setLoadingAction("disconnect");

    try {
      await disconnectInstagram(accessToken);
      setActionMessage("Instagram disconnected.");
      await queryClient.invalidateQueries({ queryKey: ["instagram-status"] });
      await queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Disconnect failed.");
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleRefresh() {
    if (!accessToken) {
      return;
    }

    setActionError("");
    setActionMessage("");
    setLoadingAction("refresh");

    try {
      await refreshInstagramToken(accessToken);
      setActionMessage("Instagram token refreshed.");
      await queryClient.invalidateQueries({ queryKey: ["instagram-status"] });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Refresh failed.");
    } finally {
      setLoadingAction(null);
    }
  }

  if (!accessToken || isLoading) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-600">Loading Instagram settings...</p>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-red-700">Could not load Instagram settings.</p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold">Instagram integration</h3>
          <p className="mt-1 text-sm text-zinc-600">
            Connect your Instagram business account to receive and send DMs.
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            data.connected
              ? "bg-emerald-100 text-emerald-700"
              : "bg-zinc-100 text-zinc-600"
          }`}
        >
          {data.connected ? "Connected" : "Not connected"}
        </span>
      </div>

      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-zinc-500">Username</dt>
          <dd className="font-medium text-zinc-900">
            {data.username ? `@${data.username}` : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Connected at</dt>
          <dd className="font-medium text-zinc-900">
            {formatDate(data.connected_at)}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">Token expires</dt>
          <dd className="font-medium text-zinc-900">
            {formatDate(data.token_expires_at)}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">OAuth mode</dt>
          <dd className="font-medium text-zinc-900">
            {data.oauth_configured ? "Meta OAuth" : "Development mock"}
          </dd>
        </div>
      </dl>

      {actionError && (
        <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </p>
      )}
      {actionMessage && (
        <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {actionMessage}
        </p>
      )}

      {data.can_manage ? (
        <div className="mt-5 flex flex-wrap gap-3">
          {!data.connected && (
            <button
              type="button"
              onClick={handleConnect}
              disabled={loadingAction !== null}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60"
            >
              {loadingAction === "connect"
                ? "Connecting..."
                : data.mock_available
                  ? "Connect (dev mock)"
                  : "Connect Instagram"}
            </button>
          )}
          {data.connected && (
            <>
              <button
                type="button"
                onClick={handleRefresh}
                disabled={loadingAction !== null}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50 disabled:opacity-60"
              >
                {loadingAction === "refresh" ? "Refreshing..." : "Refresh token"}
              </button>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={loadingAction !== null}
                className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-60"
              >
                {loadingAction === "disconnect" ? "Disconnecting..." : "Disconnect"}
              </button>
            </>
          )}
        </div>
      ) : (
        <p className="mt-5 text-sm text-zinc-600">
          Only shop admins can manage the Instagram integration.
        </p>
      )}

      {!data.oauth_configured && data.can_manage && (
        <p className="mt-4 text-xs text-zinc-500">
          Set <code className="rounded bg-zinc-100 px-1">META_APP_ID</code> and{" "}
          <code className="rounded bg-zinc-100 px-1">META_APP_SECRET</code> in the
          backend <code className="rounded bg-zinc-100 px-1">.env</code> to use real
          Meta OAuth in production.
        </p>
      )}

      {data.connected && !data.oauth_configured && data.can_manage && (
        <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          <p className="font-medium">Development mock is active</p>
          <p className="mt-1 text-blue-800">
            Real Instagram DMs require Meta app credentials and a public webhook URL.
            In dev, simulate a customer DM with:
          </p>
          <code className="mt-2 block rounded bg-white px-2 py-1 text-xs text-blue-900">
            python3 backend/manage.py simulate_instagram_inbound -u YOUR_CUSTOMER_USERNAME
          </code>
          <p className="mt-2 text-xs text-blue-800">
            Your connected account (@{data.username}) is the shop inbox — use{" "}
            <code className="rounded bg-white px-1">-u</code> for the customer who
            messages you. Retry failed webhooks with{" "}
            <code className="rounded bg-white px-1">sync_instagram_inbound</code>.
          </p>
        </div>
      )}
    </section>
  );
}

export function InstagramSettingsLink() {
  return (
    <Link
      href="/settings"
      className="text-sm font-medium text-zinc-900 underline"
    >
      Open Instagram settings
    </Link>
  );
}
