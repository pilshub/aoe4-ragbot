import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AoE4 Bot - Your AI Advisor for Age of Empires IV",
  description: "Ask anything about Age of Empires 4: civilizations, strategies, unit stats, build orders, pro players, and more.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
