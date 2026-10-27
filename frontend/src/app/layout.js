import "./globals.css";
import Header from "@/components/Header";

export const metadata = {
  title: "ByteArena",
  description: "Любительские киберспортивные турниры за пару минут",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        <Header />
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
