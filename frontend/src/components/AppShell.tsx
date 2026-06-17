import Link from "next/link";

type AppShellProps = {
  children: React.ReactNode;
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "#", label: "Chats" },
  { href: "#", label: "Clients" },
  { href: "#", label: "Orders" },
];

export function AppShell({ children }: AppShellProps) {
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
              className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4">
          <div>
            <p className="text-sm text-zinc-500">Instagram shop CRM</p>
            <h2 className="text-lg font-semibold">Dashboard</h2>
          </div>
          <div className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600">
            MVP shell
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
