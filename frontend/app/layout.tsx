import type { Metadata } from "next";
import { Merriweather } from "next/font/google";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";

const merriweather = Merriweather({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-merriweather",
});

export const metadata: Metadata = {
  title: "Descoberta musical",
  description: "Descubra músicas pelas pessoas.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${merriweather.variable} min-h-screen bg-zinc-50 text-zinc-900`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
