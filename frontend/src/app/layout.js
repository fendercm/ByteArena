import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import MockProvider from "@/components/MockProvider";

export const metadata = {
  title: "ByteArena",
  description: "Любительские киберспортивные турниры за пару минут",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        <MockProvider>
          <Header />
          <main className="container">{children}</main>
          <Footer />
        </MockProvider>
      </body>
    </html>
  );
}