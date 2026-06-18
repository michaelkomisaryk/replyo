"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";

import { searchClients, type ClientSearchResult } from "@/lib/api";

function ResultItem({
  result,
  onSelect,
}: {
  result: ClientSearchResult;
  onSelect: () => void;
}) {
  const label = result.display_name || `@${result.instagram_username}`;

  if (!result.chat_id) {
    return (
      <div className="px-4 py-3 text-sm text-zinc-500">
        {label} — no chat yet
      </div>
    );
  }

  return (
    <Link
      href={`/chats/${result.chat_id}`}
      onClick={onSelect}
      className="block px-4 py-3 transition hover:bg-zinc-50"
    >
      <p className="text-sm font-medium text-zinc-900">{label}</p>
      <p className="text-xs text-zinc-500">@{result.instagram_username}</p>
      <div className="mt-1 flex flex-wrap gap-2">
        {result.is_archived && (
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-zinc-600">
            Archived
          </span>
        )}
        {result.assigned_to_email && (
          <span className="text-[10px] text-zinc-400">
            {result.assigned_to_email}
          </span>
        )}
      </div>
    </Link>
  );
}

export function ClientSearchBar() {
  const { data: session } = useSession();
  const accessToken = session?.accessToken;
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const { data, isFetching } = useQuery({
    queryKey: ["client-search", debouncedQuery, accessToken],
    queryFn: () => searchClients(accessToken!, debouncedQuery),
    enabled: Boolean(accessToken) && debouncedQuery.length >= 2,
  });

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const showDropdown = open && debouncedQuery.length >= 2;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <label htmlFor="client-search" className="sr-only">
        Search clients
      </label>
      <input
        id="client-search"
        type="search"
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search clients..."
        className="w-full rounded-full border border-zinc-300 bg-zinc-50 px-4 py-2 text-sm outline-none focus:border-zinc-500 focus:bg-white"
      />

      {showDropdown && (
        <div className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-50 overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-lg">
          {isFetching ? (
            <p className="px-4 py-3 text-sm text-zinc-500">Searching...</p>
          ) : !data?.length ? (
            <p className="px-4 py-3 text-sm text-zinc-500">No clients found.</p>
          ) : (
            <ul className="max-h-80 divide-y divide-zinc-100 overflow-y-auto">
              {data.map((result) => (
                <li key={result.id}>
                  <ResultItem
                    result={result}
                    onSelect={() => {
                      setOpen(false);
                      setQuery("");
                    }}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
