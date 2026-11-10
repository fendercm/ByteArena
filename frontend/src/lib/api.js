export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === "string" ? detail : "Проверьте заполненные поля");
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    credentials: "include",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, body?.detail ?? "Сервер недоступен");
  if (body === null) throw new ApiError(502, "Сервер вернул неожиданный ответ");
  return body;
}

export const api = {
  getMe: () => request("/me"),
  logout: () => request("/auth/logout", { method: "POST" }),
  getTournaments: (signal) => request("/tournaments", { signal }),
  getTournament: (id, signal) => request(`/tournaments/${encodeURIComponent(id)}`, { signal }),
  createTournament: (data) =>
    request("/tournaments", { method: "POST", body: JSON.stringify(data) }),
};

export function fieldErrors(error) {
  if (!Array.isArray(error.detail)) return {};
  const errors = {};
  for (const item of error.detail) {
    const field = item.loc?.[1];
    if (!field || errors[field]) continue;
    const messages = {
      title: "Введите название от 1 до 128 символов",
      starts_at: "Укажите будущую дату и время начала",
      max_teams: "Выберите 4, 8 или 16 команд",
    };
    errors[field] = messages[field] ?? "Проверьте значение поля";
  }
  return errors;
}

export function formatDate(value) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "long",
    timeStyle: "short",
    timeZone: "Europe/Moscow",
  }).format(new Date(value));
}
