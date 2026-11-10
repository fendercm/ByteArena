const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 204) return null;

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
  return request(`/users/${id}`);
}