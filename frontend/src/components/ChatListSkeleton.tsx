export function ChatListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <div className="border-b border-zinc-100 px-5 py-4">
        <div className="h-4 w-32 animate-pulse rounded bg-zinc-200" />
      </div>
      <ul className="divide-y divide-zinc-100">
        {Array.from({ length: rows }).map((_, index) => (
          <li key={index} className="flex items-center justify-between px-5 py-4">
            <div className="space-y-2">
              <div className="h-4 w-40 animate-pulse rounded bg-zinc-200" />
              <div className="h-3 w-24 animate-pulse rounded bg-zinc-100" />
            </div>
            <div className="h-6 w-16 animate-pulse rounded-full bg-zinc-100" />
          </li>
        ))}
      </ul>
    </section>
  );
}

export function ChatDashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-9 w-24 animate-pulse rounded-full bg-zinc-200"
          />
        ))}
      </div>
      <ChatListSkeleton rows={3} />
      <ChatListSkeleton rows={2} />
    </div>
  );
}
