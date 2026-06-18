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

export { API_BASE_URL };
