import type { Metadata } from "next";
import Link from "next/link";
import { Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dental Radar",
  description: "B2B sales intelligence for dental clinics",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Dental Radar",
    description: "B2B sales intelligence for dental clinics",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:shadow"
        >
          Skip to content
        </a>
        <div className="min-h-screen bg-background">
          <header className="border-b bg-card/80 backdrop-blur">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
              <div>
                <Link href="/clinics" className="text-sm font-medium uppercase tracking-[0.2em] text-primary">
                  Dental Radar
                </Link>
                <p className="text-sm text-muted-foreground">Purchase propensity intelligence</p>
              </div>
              <nav aria-label="Primary" className="flex items-center gap-4 text-sm">
                <Link href="/clinics" className="text-foreground hover:underline">
                  Clinics
                </Link>
                <Link href="/settings/scoring" className="text-muted-foreground hover:text-foreground hover:underline">
                  Scoring settings
                </Link>
              </nav>
            </div>
          </header>
          <main id="main-content" className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
