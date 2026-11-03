import DiscordLink from "@/components/DiscordLink";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <div className="footer-brand">
          <strong>ByteArena</strong>
          <span>Любительские турниры CS2</span>
        </div>
        <div className="footer-links">
          <DiscordLink>Поддержка в Discord</DiscordLink>
          <span>© 2026</span>
        </div>
      </div>
    </footer>
  );
}
