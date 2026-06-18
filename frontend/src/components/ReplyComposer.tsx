"use client";

import { FormEvent, useState } from "react";

import { sendChatReplySafe } from "@/lib/api";

type ReplyComposerProps = {
  accessToken: string;
  chatId: number;
  onSent: () => void;
};

type ComposerStatus = "idle" | "sending" | "sent" | "failed";

export function ReplyComposer({
  accessToken,
  chatId,
  onSent,
}: ReplyComposerProps) {
  const [content, setContent] = useState("");
  const [status, setStatus] = useState<ComposerStatus>("idle");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) {
      return;
    }

    setStatus("sending");
    setError("");

    const result = await sendChatReplySafe(accessToken, chatId, trimmed);

    if (result.ok) {
      setContent("");
      setStatus("sent");
      onSent();
      window.setTimeout(() => setStatus("idle"), 2000);
      return;
    }

    setStatus("failed");
    const detail = result.error.detail || "Failed to send message.";
    setError(
      result.error.retryable
        ? `${detail} You can try again in a moment.`
        : detail,
    );
    onSent();
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-zinc-200 bg-white p-4">
      <label htmlFor="reply" className="sr-only">
        Reply
      </label>
      <textarea
        id="reply"
        rows={3}
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="Write a reply to send via Instagram..."
        className="w-full resize-none rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
        disabled={status === "sending"}
      />

      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="text-xs text-zinc-500">
          {status === "sending" && "Sending via Instagram..."}
          {status === "sent" && (
            <span className="text-emerald-700">Sent to Instagram</span>
          )}
          {status === "failed" && (
            <span className="text-red-700">{error}</span>
          )}
        </div>
        <button
          type="submit"
          disabled={status === "sending" || !content.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-60"
        >
          {status === "sending" ? "Sending..." : "Send reply"}
        </button>
      </div>
    </form>
  );
}
