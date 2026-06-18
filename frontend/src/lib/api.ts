const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type HealthResponse = {
  status: string;
};

export type AuthUser = {
  id: number;
  email: string;
  shop_name: string;
  role: string;
  is_email_verified: boolean;
};

export type RegisterResponse = {
  message: string;
  user: AuthUser;
  debug_verification_url?: string;
};

export type OnboardingStep = {
  id: string;
  label: string;
  completed: boolean;
  placeholder: boolean;
};

export type OnboardingChecklist = {
  steps: OnboardingStep[];
  completed_count: number;
  total_count: number;
  is_complete: boolean;
};

export type TeamInvitation = {
  id: number;
  email: string;
  role: string;
  accepted_at: string | null;
  expires_at: string;
  created_at: string;
  debug_accept_url?: string;
};

export type InstagramStatus = {
  connected: boolean;
  username: string | null;
  instagram_user_id: string | null;
  connected_at: string | null;
  token_expires_at: string | null;
  can_manage: boolean;
  oauth_configured: boolean;
  mock_available: boolean;
};

export type InstagramConnectResponse = {
  authorization_url: string | null;
  mock_available: boolean;
  detail?: string;
};

export type Chat = {
  id: number;
  shop: number;
  client: number;
  client_username: string;
  client_display_name: string;
  assigned_to: number | null;
  assigned_to_email: string | null;
  priority: string;
  priority_label: string;
  wait_seconds: number | null;
  wait_urgency: "yellow" | "orange" | "red" | null;
  is_pinned: boolean;
  is_archived: boolean;
  archived_at: string | null;
  has_new_message_badge: boolean;
  created_at: string;
  updated_at: string;
};

export type ChatPriorityBucket = {
  priority: string;
  label: string;
  count: number;
  chats: Chat[];
};

export type ChatPrioritiesResponse = {
  wait_threshold_seconds: number;
  buckets: ChatPriorityBucket[];
};

export type ChatListView = "active" | "archived" | "rejected" | "all";

export type Message = {
  id: number;
  chat: number;
  direction: "inbound" | "outbound";
  content: string;
  sent_at: string;
  external_id: string;
  delivery_status: "" | "sending" | "sent" | "failed";
  delivery_error: string;
  created_at: string;
  updated_at: string;
};

export type SendReplyResponse = Message;

export type SendReplyError = {
  detail: string;
  retryable?: boolean;
  message?: Message;
};

export type ClientOrderSummary = {
  id: number;
  status: string;
  status_label: string;
  chat: number | null;
  created_at: string;
  updated_at: string;
};

export type ClientCard = {
  id: number;
  shop: number;
  instagram_username: string;
  instagram_user_id: string;
  display_name: string;
  notes: string;
  orders: ClientOrderSummary[];
  can_edit: boolean;
  created_at: string;
  updated_at: string;
};

export type ClientSearchResult = {
  id: number;
  instagram_username: string;
  display_name: string;
  chat_id: number | null;
  is_archived: boolean;
  assigned_to_email: string | null;
};

export type Order = {
  id: number;
  shop: number;
  client: number;
  chat: number | null;
  status: string;
  status_label: string;
  created_at: string;
  updated_at: string;
};

export type ChatNotification = {
  id: number;
  chat_id: number;
  client_username: string;
  client_display_name: string;
  kind: string;
  kind_label: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type NotificationListResponse = {
  unread_count: number;
  results: ChatNotification[];
};

async function authFetch(path: string, accessToken: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(options.headers ?? {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Object.values(data).flat().join(", ") || "Request failed.";
    throw new Error(detail);
  }

  return data;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function registerShop(input: {
  shop_name: string;
  email: string;
  password: string;
}): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.email?.[0] ?? data.detail ?? "Registration failed.");
  }

  return data as RegisterResponse;
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/auth/verify-email/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "Email verification failed.");
  }

  return data as { message: string };
}

export async function fetchOnboarding(
  accessToken: string,
): Promise<OnboardingChecklist> {
  return authFetch("/api/onboarding/", accessToken) as Promise<OnboardingChecklist>;
}

export async function inviteTeamMember(
  accessToken: string,
  input: { email: string; role: "manager" | "support_manager" },
): Promise<TeamInvitation> {
  return authFetch("/api/invitations/", accessToken, {
    method: "POST",
    body: JSON.stringify(input),
  }) as Promise<TeamInvitation>;
}

export async function acceptInvitation(input: {
  token: string;
  password: string;
}): Promise<{
  message: string;
  access: string;
  refresh: string;
  user: AuthUser;
}> {
  const response = await fetch(`${API_BASE_URL}/api/invitations/accept/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(
      data.token?.[0] ?? data.detail ?? "Failed to accept invitation.",
    );
  }

  return data;
}

export async function fetchInstagramStatus(
  accessToken: string,
): Promise<InstagramStatus> {
  return authFetch(
    "/api/integrations/instagram/status/",
    accessToken,
  ) as Promise<InstagramStatus>;
}

export async function fetchInstagramConnectUrl(
  accessToken: string,
): Promise<InstagramConnectResponse> {
  return authFetch(
    "/api/integrations/instagram/connect/",
    accessToken,
  ) as Promise<InstagramConnectResponse>;
}

export async function mockConnectInstagram(
  accessToken: string,
): Promise<InstagramStatus> {
  return authFetch("/api/integrations/instagram/mock-connect/", accessToken, {
    method: "POST",
  }) as Promise<InstagramStatus>;
}

export async function disconnectInstagram(
  accessToken: string,
): Promise<{ message: string }> {
  return authFetch("/api/integrations/instagram/disconnect/", accessToken, {
    method: "POST",
  }) as Promise<{ message: string }>;
}

export async function refreshInstagramToken(
  accessToken: string,
): Promise<InstagramStatus> {
  return authFetch("/api/integrations/instagram/refresh/", accessToken, {
    method: "POST",
  }) as Promise<InstagramStatus>;
}

export async function fetchChats(
  accessToken: string,
  options: {
    view?: ChatListView;
    priority?: string;
    assignedTo?: string;
  } = {},
): Promise<Chat[]> {
  const params = new URLSearchParams();
  if (options.view) {
    params.set("view", options.view);
  }
  if (options.priority) {
    params.set("priority", options.priority);
  }
  if (options.assignedTo) {
    params.set("assigned_to", options.assignedTo);
  }

  const query = params.toString();
  const path = query ? `/api/chats/?${query}` : "/api/chats/";
  return authFetch(path, accessToken) as Promise<Chat[]>;
}

export async function fetchChatPriorities(
  accessToken: string,
  options: { assignedTo?: string } = {},
): Promise<ChatPrioritiesResponse> {
  const params = new URLSearchParams();
  if (options.assignedTo) {
    params.set("assigned_to", options.assignedTo);
  }
  const query = params.toString();
  const path = query
    ? `/api/chats/priorities/?${query}`
    : "/api/chats/priorities/";
  return authFetch(path, accessToken) as Promise<ChatPrioritiesResponse>;
}

export type TeamMember = {
  id: number;
  email: string;
  role: string;
  username: string;
};

export async function fetchTeamMembers(accessToken: string): Promise<TeamMember[]> {
  return authFetch("/api/users/?team=1", accessToken) as Promise<TeamMember[]>;
}

export async function pinChat(
  accessToken: string,
  chatId: number,
  pinned: boolean,
): Promise<Chat> {
  return authFetch(`/api/chats/${chatId}/pin/`, accessToken, {
    method: "POST",
    body: JSON.stringify({ pinned }),
  }) as Promise<Chat>;
}

export async function archiveChat(
  accessToken: string,
  chatId: number,
): Promise<Chat> {
  return authFetch(`/api/chats/${chatId}/archive/`, accessToken, {
    method: "POST",
  }) as Promise<Chat>;
}

export async function assignChat(
  accessToken: string,
  chatId: number,
  assignedTo: number | null,
): Promise<Chat> {
  return authFetch(`/api/chats/${chatId}/assign/`, accessToken, {
    method: "POST",
    body: JSON.stringify({ assigned_to: assignedTo }),
  }) as Promise<Chat>;
}

export async function escalateChat(
  accessToken: string,
  chatId: number,
): Promise<Chat> {
  return authFetch(`/api/chats/${chatId}/escalate/`, accessToken, {
    method: "POST",
  }) as Promise<Chat>;
}

export async function fetchChat(
  accessToken: string,
  chatId: number,
): Promise<Chat> {
  return authFetch(`/api/chats/${chatId}/`, accessToken) as Promise<Chat>;
}

export async function fetchMessages(
  accessToken: string,
  chatId: number,
): Promise<Message[]> {
  return authFetch(
    `/api/messages/?chat=${chatId}`,
    accessToken,
  ) as Promise<Message[]>;
}

export async function sendChatReply(
  accessToken: string,
  chatId: number,
  content: string,
): Promise<SendReplyResponse> {
  return authFetch(`/api/chats/${chatId}/reply/`, accessToken, {
    method: "POST",
    body: JSON.stringify({ content }),
  }) as Promise<SendReplyResponse>;
}

export async function sendChatReplySafe(
  accessToken: string,
  chatId: number,
  content: string,
): Promise<{ ok: true; message: Message } | { ok: false; error: SendReplyError }> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/reply/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ content }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    return {
      ok: false,
      error: data as SendReplyError,
    };
  }

  return { ok: true, message: data as Message };
}

export async function fetchClientCard(
  accessToken: string,
  clientId: number,
): Promise<ClientCard> {
  return authFetch(
    `/api/clients/${clientId}/card/`,
    accessToken,
  ) as Promise<ClientCard>;
}

export async function searchClients(
  accessToken: string,
  query: string,
): Promise<ClientSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  return authFetch(
    `/api/clients/search/?${params.toString()}`,
    accessToken,
  ) as Promise<ClientSearchResult[]>;
}

export async function updateClientNotes(
  accessToken: string,
  clientId: number,
  notes: string,
): Promise<ClientCard> {
  return authFetch(`/api/clients/${clientId}/card/`, accessToken, {
    method: "PATCH",
    body: JSON.stringify({ notes }),
  }) as Promise<ClientCard>;
}

export async function fetchChatOrders(
  accessToken: string,
  chatId: number,
): Promise<Order[]> {
  return authFetch(
    `/api/orders/?chat=${chatId}`,
    accessToken,
  ) as Promise<Order[]>;
}

export async function createChatOrder(
  accessToken: string,
  chatId: number,
  status: string = "waiting_payment",
): Promise<Order> {
  return authFetch(`/api/chats/${chatId}/orders/`, accessToken, {
    method: "POST",
    body: JSON.stringify({ status }),
  }) as Promise<Order>;
}

export async function updateOrderStatus(
  accessToken: string,
  orderId: number,
  status: string,
): Promise<Order> {
  return authFetch(`/api/orders/${orderId}/`, accessToken, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  }) as Promise<Order>;
}

export async function fetchNotifications(
  accessToken: string,
  unreadOnly = false,
): Promise<NotificationListResponse> {
  const path = unreadOnly
    ? "/api/notifications/?unread=true"
    : "/api/notifications/";
  return authFetch(path, accessToken) as Promise<NotificationListResponse>;
}

export async function markNotificationRead(
  accessToken: string,
  notificationId: number,
): Promise<ChatNotification> {
  return authFetch(
    `/api/notifications/${notificationId}/read/`,
    accessToken,
    { method: "POST" },
  ) as Promise<ChatNotification>;
}

export async function markAllNotificationsRead(
  accessToken: string,
): Promise<{ marked_read: number }> {
  return authFetch("/api/notifications/read-all/", accessToken, {
    method: "POST",
  }) as Promise<{ marked_read: number }>;
}

export { API_BASE_URL };
