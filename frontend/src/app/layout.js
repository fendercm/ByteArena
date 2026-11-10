import "./globals.css";
import Header from "@/components/Header";
import AuthProvider from "@/components/AuthProvider";

export const metadata = {
  title: "ByteArena",
  description: "Любительские киберспортивные турниры за пару минут",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        <AuthProvider>
          <Header />
          <main className="container main-content">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
