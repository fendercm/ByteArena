import Link from "next/link";
import DiscordLink from "@/components/DiscordLink";
import TournamentList from "@/components/TournamentList";
import { homeTournaments } from "@/data/home-tournaments";

export default function HomePage() {
  return (
    <>
      <section className="home-intro">
        <h1>Турниры CS2</h1>
        <p>Создай турнир или присоединяйся к ближайшему.</p>
        <div className="intro-actions">
          <Link href="/tournaments/new" className="button">
            + Создать турнир
          </Link>
          <DiscordLink className="button button-secondary">Наш Discord</DiscordLink>
        </div>
      </section>
      <TournamentList tournaments={homeTournaments} />
    </>
  );
}
