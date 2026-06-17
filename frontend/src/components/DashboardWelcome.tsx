"use client";

import { useSession } from "next-auth/react";

export function DashboardWelcome() {
  const { data: session } = useSession();

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <h3 className="text-base font-semibold">Welcome to Replyo</h3>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
        {session?.user?.email
          ? `Signed in as ${session.user.email}. Your dashboard is ready.`
          : "Your MicroCRM dashboard is ready."}
      </p>
      {session?.user?.isEmailVerified === false && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Please verify your email to complete account setup.
        </p>
      )}
    </section>
  );
}
