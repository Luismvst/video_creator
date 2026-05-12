"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createProject } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const p = await createProject(name.trim() || "Sin título");
      router.push(`/projects/${p.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Nuevo proyecto</h1>
      <form onSubmit={onSubmit} className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <div>
          <label className="block text-sm font-medium text-zinc-200">Nombre del proyecto</label>
          <input
            className="mt-2 w-full rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] px-3 py-2 text-sm text-white outline-none focus:border-[var(--vz-accent)]"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ej. Single · Primavera 2026"
            autoFocus
          />
        </div>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Creando…" : "Crear y continuar"}
        </button>
      </form>
    </div>
  );
}
