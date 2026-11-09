import users from "../../mocks/data/users.json";

export const authMocksEnabled = process.env.NEXT_PUBLIC_API_MOCKS === "true";
export const discordLoginUrl = "/api/auth/discord/login";

const mockSessionKey = "bytearena:mock-session";

export function signInAsDemoUser() {
  sessionStorage.setItem(mockSessionKey, "active");
  return users[0];
}

export async function getCurrentUser(signal) {
  if (authMocksEnabled) {
    return sessionStorage.getItem(mockSessionKey) === "active" ? users[0] : null;
  }

  const response = await fetch("/api/me", {
    credentials: "same-origin",
    cache: "no-store",
    signal,
  });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error("Не удалось загрузить профиль");
  return response.json();
}

export async function signOut() {
  if (authMocksEnabled) {
    sessionStorage.removeItem(mockSessionKey);
    return;
  }

  const response = await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  if (!response.ok && response.status !== 401)
    throw new Error("Не удалось выйти. Попробуй ещё раз.");
}
