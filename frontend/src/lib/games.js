// Игры, для которых можно провести турнир. Название берём по полю game турнира,
// чтобы на страницах не было зашитого «CS2»: новая игра добавляется одной строкой здесь.
export const games = {
  cs2: { short: "CS2", name: "Counter-Strike 2", format: "5×5" },
};

// Игра, которую бэкенд ставит новому турниру по умолчанию
export const defaultGame = "cs2";

// Неизвестная игра показывается как есть, без формата
export function gameInfo(game) {
  return games[game] ?? { short: game ?? "", name: game ?? "", format: "" };
}
