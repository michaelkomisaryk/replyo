"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { fetchInstagramStatus } from "@/lib/api";

export function InstagramConnectionBadge() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;

  const { data, isLoading } = useQuery({
    queryKey: ["instagram-status", accessToken],
    queryFn: () => fetchInstagramStatus(accessToken!),
    enabled: Boolean(accessToken),
  });

  if (!accessToken || isLoading || !data) {
    return null;
  }

  return (
    <Link
      href="/settings"
      className={`rounded-full px-3 py-1 text-xs font-medium transition hover:opacity-80 ${
        data.connected
          ? "bg-emerald-100 text-emerald-700"
          : "bg-amber-100 text-amber-800"
      }`}
    >
      {data.connected
        ? `Instagram: @${data.username}`
        : "Instagram not connected"}
    </Link>
  );
}
