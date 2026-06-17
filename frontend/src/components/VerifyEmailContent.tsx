"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { verifyEmail } from "@/lib/api";

export function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const pending = searchParams.get("pending");

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    token ? "loading" : "idle",
  );
  const [message, setMessage] = useState(
    pending
      ? "Check your email for a verification link."
      : "Verify your email to complete registration.",
  );

  useEffect(() => {
    if (!token) {
      return;
    }

    verifyEmail(token)
      .then((result) => {
        setStatus("success");
        setMessage(result.message);
      })
      .catch((error: Error) => {
        setStatus("error");
        setMessage(error.message);
      });
  }, [token]);

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
      <h1 className="text-2xl font-semibold">Email verification</h1>
      <p
        className={`mt-4 text-sm ${
          status === "error"
            ? "text-red-700"
            : status === "success"
              ? "text-emerald-700"
              : "text-zinc-600"
        }`}
      >
        {status === "loading" ? "Verifying your email..." : message}
      </p>

      <div className="mt-6">
        <Link
          href="/login"
          className="text-sm font-medium text-zinc-900 underline"
        >
          Continue to sign in
        </Link>
      </div>
    </div>
  );
}
