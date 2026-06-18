import { MessageThreadSkeleton } from "@/components/MessageThread";

export function ChatDetailSkeleton() {
  return (
    <div className="grid h-[calc(100vh-8rem)] gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <div className="h-3 w-20 animate-pulse rounded bg-zinc-100" />
          <div className="mt-2 h-5 w-48 animate-pulse rounded bg-zinc-200" />
          <div className="mt-1 h-4 w-32 animate-pulse rounded bg-zinc-100" />
        </div>
        <MessageThreadSkeleton />
        <div className="border-t border-zinc-200 p-4">
          <div className="h-20 animate-pulse rounded-lg bg-zinc-100" />
        </div>
      </div>
      <div className="space-y-4">
        <div className="h-40 animate-pulse rounded-2xl bg-zinc-200" />
        <div className="h-48 animate-pulse rounded-2xl bg-zinc-200" />
        <div className="h-64 animate-pulse rounded-2xl bg-zinc-200" />
      </div>
    </div>
  );
}
