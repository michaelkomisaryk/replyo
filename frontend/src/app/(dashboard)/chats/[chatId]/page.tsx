import { ChatDetail } from "@/components/ChatDetail";

type ChatDetailPageProps = {
  params: Promise<{ chatId: string }>;
};

export default async function ChatDetailPage({ params }: ChatDetailPageProps) {
  const { chatId } = await params;
  const id = Number(chatId);

  return <ChatDetail chatId={id} />;
}
