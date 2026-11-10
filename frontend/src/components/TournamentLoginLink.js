"use client";

export const loginReturnKey = "bytearena:return-to-create";

export default function TournamentLoginLink() {
  function rememberReturn() {
    try {
      sessionStorage.setItem(loginReturnKey, String(Date.now() + 10 * 60 * 1000));
    } catch {
      // После входа можно вернуться через пункт «Организатор» в шапке.
    }
  }

  return (
    <a className="button" href="/api/auth/discord/login" onClick={rememberReturn}>
      Войти через Discord
    </a>
  );
}
