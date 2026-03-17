import type { Metadata } from "next";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { Providers } from "@/app/providers";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "SocialGH — Платформа для команд и проектов",
  description: "Находите проекты, создавайте команды, откликайтесь на позиции",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="flex min-h-screen flex-col">
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
