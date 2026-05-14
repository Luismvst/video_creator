import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Bienvenido</h1>
        <p className="mt-2 text-[var(--vz-muted)]">
          <strong className="text-zinc-200">VideoZero</strong> es un director creativo{" "}
          <strong className="text-zinc-200">guiado por la letra</strong>. Crea un proyecto, pega tu letra y completa el
          setup (metadata, duración objetivo opcional, audio opcional, declaraciones de derechos).
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link
          href="/projects/new"
          className="inline-flex rounded-lg bg-[var(--vz-accent)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          Nuevo proyecto
        </Link>
        <Link
          href="/projects"
          className="inline-flex rounded-lg border border-[var(--vz-border)] px-4 py-2.5 text-sm font-medium text-zinc-200 hover:border-[var(--vz-accent)]"
        >
          Ver proyectos
        </Link>
      </div>
    </div>
  );
}
