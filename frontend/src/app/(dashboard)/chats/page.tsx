import { ChatList } from "@/components/ChatList";

export default function ChatsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Chats</h1>
        <p className="mt-1 text-sm text-zinc-600">
          View Instagram conversations and reply to clients.
        </p>
      </div>
      <ChatList />
    </div>
  );
}
