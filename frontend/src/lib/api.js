const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
const API_PREFIX = "/api";

async function request(endpoint, options = {}) {
  const normalizedEndpoint = endpoint.startsWith("/")
    ? endpoint
    : `/${endpoint}`;

  const response = await fetch(
    `${API_URL}${API_PREFIX}${normalizedEndpoint}`,
    {
      credentials: "include",
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    },
  );

  if (!response.ok) {
    const error = new Error(`API error: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;

  return response.json();
}

export function getCurrentUser() {
  return request("/me");
}

export function logout() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export function getUserProfile(id) {
  return request(`/users/${encodeURIComponent(id)}`);
}

export async function getTournaments(status, signal) {
  if (process.env.NEXT_PUBLIC_API_MOCKS === "true") {
    const { homeTournaments } = await import("@/data/home-tournaments");
    const items = homeTournaments.filter(
      (tournament) => tournament.status === status,
    );
    return { items, total: items.length };
  }

  const data = await request(
    `/tournaments?status=${encodeURIComponent(status)}`,
    {
      cache: "no-store",
      signal,
    },
  );

  if (!Array.isArray(data.items)) {
    throw new Error("Некорректный список турниров");
  }

  return data;
}
