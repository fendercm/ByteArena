export default function DiscordLink({ children, className = "" }) {
  const url = process.env.NEXT_PUBLIC_DISCORD_URL;
  return url ? (
    <a href={url} className={className} target="_blank" rel="noreferrer">
      {children}
    </a>
  ) : (
    <span className={className} title="Ссылка на Discord скоро появится" aria-disabled="true">
      {children}
    </span>
  );
}
