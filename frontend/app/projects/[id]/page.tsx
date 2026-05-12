"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { ProjectDetail } from "@/lib/api";
import { enqueueAnalysis, getProject, patchSong, uploadAudio } from "@/lib/api";

export default function ProjectSongSetupPage() {
  const params = useParams();
  const id = Number(params.id);
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [stubMsg, setStubMsg] = useState<string | null>(null);

  const title = data?.song?.title ?? "";
  const artist = data?.song?.artist ?? "";
  const language = data?.song?.language ?? "";
  const mood = data?.song?.mood ?? "";
  const lyrics = data?.song?.lyrics_text ?? "";
  const rights = data?.song?.audio_rights_confirmed ?? false;

  const load = useCallback(async () => {
    setError(null);
    try {
      const p = await getProject(id);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar");
    }
  }, [id]);

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    void load();
  }, [id, load]);

  async function save(partial: Parameters<typeof patchSong>[1]) {
    if (!Number.isFinite(id)) return;
    setSaving(true);
    setError(null);
    try {
      const p = await patchSong(id, partial);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  async function onAudioChange(file: File | null) {
    if (!file || !Number.isFinite(id)) return;
    setSaving(true);
    setError(null);
    try {
      const p = await uploadAudio(id, file);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al subir audio");
    } finally {
      setSaving(false);
    }
  }

  async function tryEnqueue() {
    if (!Number.isFinite(id)) return;
    setStubMsg(null);
    setError(null);
    try {
      const r = await enqueueAnalysis(id);
      setStubMsg(`${r.status}: ${r.message}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo encolar");
    }
  }

  if (!Number.isFinite(id)) {
    return <p className="text-red-400">ID inválido</p>;
  }

  if (!data && !error) {
    return <p className="text-[var(--vz-muted)]">Cargando…</p>;
  }

  if (error && !data) {
    return (
      <div className="space-y-4">
        <p className="text-red-400">{error}</p>
        <Link href="/" className="text-sm text-[var(--vz-accent)]">
          Volver al inicio
        </Link>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-[var(--vz-muted)]">Song Setup</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">{data.name}</h1>
        <p className="mt-2 text-sm text-[var(--vz-muted)]">
          Guarda letra y metadata. Sube audio. Marca la confirmación legal antes de cualquier análisis pesado (Fase 2).
        </p>
      </div>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Metadata</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Título" htmlFor="f-title">
            <input
              className="vz-input"
              defaultValue={title}
              key={`title-${data.song?.updated_at}`}
              id="f-title"
            />
          </Field>
          <Field label="Artista" htmlFor="f-artist">
            <input className="vz-input" defaultValue={artist} key={`artist-${data.song?.updated_at}`} id="f-artist" />
          </Field>
          <Field label="Idioma (ISO o libre)" htmlFor="f-lang">
            <input className="vz-input" defaultValue={language} key={`lang-${data.song?.updated_at}`} id="f-lang" />
          </Field>
          <Field label="Mood objetivo" htmlFor="f-mood">
            <input className="vz-input" defaultValue={mood} key={`mood-${data.song?.updated_at}`} id="f-mood" />
          </Field>
        </div>
        <Field label="Letra" htmlFor="f-lyrics">
          <textarea
            className="vz-input min-h-[180px] font-mono text-sm"
            defaultValue={lyrics}
            key={`lyrics-${data.song?.updated_at}`}
            id="f-lyrics"
          />
        </Field>
        <button
          type="button"
          disabled={saving}
          onClick={() => {
            const g = (n: string) => (document.getElementById(n) as HTMLInputElement | HTMLTextAreaElement).value;
            void save({
              title: g("f-title") || null,
              artist: g("f-artist") || null,
              language: g("f-lang") || null,
              mood: g("f-mood") || null,
              lyrics_text: g("f-lyrics") || null,
            });
          }}
          className="rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
        >
          {saving ? "Guardando…" : "Guardar metadata y letra"}
        </button>
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Audio</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Estado:{" "}
          {data.song?.has_audio ? (
            <span className="text-emerald-400">Archivo cargado ({data.song.audio_original_filename})</span>
          ) : (
            <span className="text-amber-300">Sin archivo</span>
          )}
        </p>
        <input
          type="file"
          accept="audio/*,.mp3,.wav,.flac,.m4a,.aac,.ogg,.webm"
          disabled={saving}
          onChange={(e) => void onAudioChange(e.target.files?.[0] ?? null)}
          className="text-sm text-[var(--vz-muted)] file:mr-4 file:rounded-lg file:border-0 file:bg-[var(--vz-accent)] file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
        />
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Derechos del audio (OPS-01)</h2>
        <label className="flex cursor-pointer items-start gap-3 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={rights}
            disabled={saving}
            onChange={(e) => void save({ audio_rights_confirmed: e.target.checked })}
            className="mt-1 h-4 w-4 rounded border-[var(--vz-border)]"
          />
          <span>
            Confirmo que tengo derecho a usar este audio en este flujo (propiedad o licencia válida). Sin esta marca,
            VideoZero no debe encolar análisis pesado.
          </span>
        </label>
      </section>

      <section className="space-y-3 rounded-xl border border-dashed border-[var(--vz-border)] bg-[var(--vz-bg)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Comprobación de gate (stub Fase 2)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Llama al endpoint de encolado. Debe fallar con 400 si falta audio o confirmación legal.
        </p>
        <button
          type="button"
          onClick={() => void tryEnqueue()}
          className="rounded-lg border border-[var(--vz-border)] px-4 py-2 text-sm text-zinc-200 hover:border-[var(--vz-accent)]"
        >
          Probar POST /analysis/enqueue
        </button>
        {stubMsg ? <p className="text-sm text-emerald-400">{stubMsg}</p> : null}
      </section>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <Link href="/" className="inline-block text-sm text-[var(--vz-muted)] hover:text-white">
        ← Volver al inicio
      </Link>
    </div>
  );
}

function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm" htmlFor={htmlFor}>
      <span className="font-medium text-zinc-200">{label}</span>
      {children}
    </label>
  );
}
