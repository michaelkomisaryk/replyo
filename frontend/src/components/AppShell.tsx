"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

import { ClientSearchBar } from "@/components/ClientSearchBar";
import { InstagramConnectionBadge } from "@/components/InstagramConnectionBadge";
import { NotificationBell } from "@/components/NotificationBell";

type AppShellProps = {
  children: React.ReactNode;
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/chats", label: "Chats" },
  { href: "/settings", label: "Settings" },
  { href: "/clients", label: "Clients" },
  { href: "/orders", label: "Orders" },
];

export function AppShell({ children }: AppShellProps) {
  const { data: session } = useSession();
  const pathname = usePathname();
  const pageTitle = pathname.startsWith("/chats/")
    ? "Chat"
    : navItems.find((item) => item.href === pathname)?.label ?? "Dashboard";

  return (
    <div className="flex min-h-screen bg-zinc-50 text-zinc-900">
      <aside className="flex w-64 flex-col border-r border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Replyo
          </p>
          <h1 className="text-lg font-semibold">MicroCRM</h1>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-4">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                pathname === item.href ||
                (item.href === "/chats" && pathname.startsWith("/chats"))
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-700 hover:bg-zinc-100"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex flex-col gap-4 border-b border-zinc-200 bg-white px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm text-zinc-500">Instagram shop CRM</p>
            <h2 className="text-lg font-semibold">{pageTitle}</h2>
          </div>
          <div className="flex flex-1 flex-col gap-3 lg:max-w-xl lg:flex-row lg:items-center lg:justify-end">
            <ClientSearchBar />
            <div className="flex items-center gap-3">
            <NotificationBell />
            <InstagramConnectionBadge />
            {session?.user?.email && (
              <span className="text-sm text-zinc-600">{session.user.email}</span>
            )}
            <button
              type="button"
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="rounded-full bg-zinc-900 px-3 py-1 text-xs font-medium text-white transition hover:bg-zinc-700"
            >
              Log out
            </button>
            </div>
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
