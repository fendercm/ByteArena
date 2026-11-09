export async function getTournaments(status, signal) {
  if (process.env.NEXT_PUBLIC_API_MOCKS === "true") {
    const { homeTournaments } = await import("@/data/home-tournaments");
    const items = homeTournaments.filter((tournament) => tournament.status === status);
    return { items, total: items.length };
  }

  const response = await fetch(`/api/tournaments?status=${encodeURIComponent(status)}`, {
    credentials: "same-origin",
    cache: "no-store",
    signal,
  });
  if (!response.ok) throw new Error("Не удалось загрузить турниры");
  const data = await response.json();
  if (!Array.isArray(data.items)) throw new Error("Некорректный список турниров");
  return data;
}
