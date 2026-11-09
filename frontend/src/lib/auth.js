export const discordLoginUrl = "/api/auth/discord/login";

export async function getCurrentUser(signal) {
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
  const response = await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  if (!response.ok && response.status !== 401)
    throw new Error("Не удалось выйти. Попробуй ещё раз.");
}
