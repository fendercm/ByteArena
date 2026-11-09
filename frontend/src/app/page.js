import Link from "next/link";
import DiscordLink from "@/components/DiscordLink";
import HomeTournaments from "@/components/HomeTournaments";

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
      <HomeTournaments />
    </>
  );
}
