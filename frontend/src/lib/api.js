const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
const API_PREFIX = "/api";

async function request(endpoint, options = {}) {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const response = await fetch(`${API_URL}${API_PREFIX}${normalizedEndpoint}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

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
