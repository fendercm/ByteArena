import Link from "next/link";

export default function Header() {
  return (
    <header
      className="container"
      style={{ display: "flex", gap: 16, alignItems: "center", padding: "16px" }}
    >
      <Link href="/">
        <strong>ByteArena</strong>
      </Link>
      <Link href="/tournaments/new">Создать турнир</Link>
      {/* Вход заработает на неделе 2 (задача B) */}
      <a href="/api/auth/discord/login" style={{ marginLeft: "auto" }}>
        Войти через Discord
      </a>
    </header>
  );
}
