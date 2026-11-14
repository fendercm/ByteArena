import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import AuthProvider from "@/components/AuthProvider";
import MockProvider from "@/components/MockProvider";

export const metadata = {
  title: "ByteArena",
  description: "Любительские киберспортивные турниры за пару минут",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        {/* MockProvider снаружи: при включённых моках AuthProvider спрашивает /api/me уже у MSW */}
        <MockProvider>
          <AuthProvider>
            <Header />
            <main className="container">{children}</main>
            <Footer />
          </AuthProvider>
        </MockProvider>
      </body>
    </html>
  );
}
