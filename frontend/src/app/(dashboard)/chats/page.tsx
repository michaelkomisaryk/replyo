import { ChatList } from "@/components/ChatList";

export default function ChatsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Chats</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Prioritized inbox for Instagram conversations — new clients and waiting
          replies appear first.
        </p>
      </div>
      <ChatList />
    </div>
  );
}
