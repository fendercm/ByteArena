import Link from "next/link";
import DiscordLink from "@/components/DiscordLink";
import HeaderAccount from "@/components/HeaderAccount";

export default function Header() {
  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link href="/" className="brand">
          <span className="brand-mark" aria-hidden="true">
            B
          </span>
          ByteArena
        </Link>
        <nav className="main-nav" aria-label="Основная навигация">
          <Link href="/">Турниры</Link>
          <Link href="/api/auth/discord/login">Моя команда</Link>
          <Link href="/tournaments/new">Организатор</Link>
        </nav>
        <div className="header-actions">
          <DiscordLink className="discord-nav">Discord</DiscordLink>
          <HeaderAccount />
        </div>
      </div>
    </header>
  );
}
