import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ProjectRow = { id: number; name: string; created_at: string };

export default async function ProjectsListPage() {
  let projects: ProjectRow[] = [];
  let err: string | null = null;
  try {
    const res = await fetch(`${API_BASE}/projects`, { cache: "no-store" });
    if (!res.ok) throw new Error(await res.text());
    projects = (await res.json()) as ProjectRow[];
  } catch (e) {
    err = e instanceof Error ? e.message : "Error";
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-white">Proyectos</h1>
        <Link href="/projects/new" className="text-sm text-[var(--vz-accent)] hover:underline">
          Nuevo
        </Link>
      </div>
      {err ? <p className="text-sm text-red-400">{err}</p> : null}
      {!err && projects.length === 0 ? (
        <p className="text-[var(--vz-muted)]">Aún no hay proyectos.</p>
      ) : null}
      <ul className="divide-y divide-[var(--vz-border)] rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)]">
        {projects.map((p) => (
          <li key={p.id}>
            <Link href={`/projects/${p.id}`} className="flex flex-col gap-1 px-4 py-3 hover:bg-[var(--vz-bg)]">
              <span className="font-medium text-white">{p.name}</span>
              <span className="text-xs text-[var(--vz-muted)]">#{p.id}</span>
            </Link>
          </li>
        ))}
      </ul>
      <Link href="/" className="text-sm text-[var(--vz-muted)] hover:text-white">
        ← Inicio
      </Link>
    </div>
  );
}
