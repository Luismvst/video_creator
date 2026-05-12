import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VideoZero",
  description: "Dirección guiada de videoclips con IA",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen">
        <header className="border-b border-[var(--vz-border)] bg-[var(--vz-card)]">
          <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
            <a href="/" className="text-lg font-semibold tracking-tight text-white">
              VideoZero
            </a>
            <span className="text-xs text-[var(--vz-muted)]">Fase 1 · Song Setup</span>
          </div>
        </header>
        <main className="mx-auto max-w-3xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
