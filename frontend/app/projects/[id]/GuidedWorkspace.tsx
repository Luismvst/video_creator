"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { ProjectDetail } from "@/lib/api";
import {
  API_BASE,
  applyOnboardingBrief,
  applyOnboardingSections,
  enqueueAnalysis,
  generateLyricInsights,
  getDocumentsPreview,
  getLyricLines,
  getProject,
  lockCreative,
  patchSong,
  unlockCreative,
  uploadAudio,
} from "@/lib/api";

const STEPS = [
  "Bienvenida",
  "Letra y canción",
  "Visión del videoclip",
  "Estructura e ideas",
  "Cerrar y exportar",
];

function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm" htmlFor={htmlFor}>
      <span className="font-medium text-zinc-200">{label}</span>
      {children}
    </label>
  );
}

export default function GuidedWorkspace() {
  const params = useParams();
  const id = Number(params.id);
  const [step, setStep] = useState(0);
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lines, setLines] = useState<{ index: number; text: string }[]>([]);
  const [stubMsg, setStubMsg] = useState<string | null>(null);
  const [docPeek, setDocPeek] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [mood, setMood] = useState("");
  const [language, setLanguage] = useState("");
  const [lyrics, setLyrics] = useState("");
  const [lyricsRights, setLyricsRights] = useState(false);
  const [pacing, setPacing] = useState("");
  const [duration, setDuration] = useState("");

  const [visionBrief, setVisionBrief] = useState("");
  const [iaMode, setIaMode] = useState<"auto" | "heuristic" | "llm">("auto");
  const [lastHint, setLastHint] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!Number.isFinite(id)) return;
    setError(null);
    try {
      const p = await getProject(id);
      setData(p);
      const s = p.song;
      if (s) {
        setTitle(s.title ?? "");
        setArtist(s.artist ?? "");
        setMood(s.mood ?? "");
        setLanguage(s.language ?? "");
        setLyrics(s.lyrics_text ?? "");
        setLyricsRights(s.lyrics_rights_confirmed);
        setPacing(s.pacing_profile ?? "");
        setDuration(s.target_duration_seconds != null ? String(s.target_duration_seconds) : "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!Number.isFinite(id) || !data?.song) return;
    let c = false;
    void getLyricLines(id)
      .then((r) => {
        if (!c) setLines(r.lines);
      })
      .catch(() => {
        if (!c) setLines([]);
      });
    return () => {
      c = true;
    };
  }, [id, data?.song?.updated_at, data?.song]);

  const locked = data?.song?.creative_locked ?? false;
  const warns = data?.song?.structure_warnings ?? [];
  const nSec = data?.song?.sections?.length ?? 0;
  const nIns = data?.song?.insights?.length ?? 0;

  const intakePreview = useMemo(() => {
    try {
      const raw = data?.song?.creative_intake_json;
      if (!raw?.trim()) return null;
      const o = JSON.parse(raw) as { reference_notes?: string };
      return o.reference_notes?.slice(0, 280) ?? null;
    } catch {
      return null;
    }
  }, [data?.song?.creative_intake_json]);

  async function saveBasics() {
    if (!Number.isFinite(id)) return;
    let dur: number | null = null;
    const d = duration.trim();
    if (d) {
      const n = Number.parseFloat(d);
      if (!Number.isFinite(n) || n <= 0) {
        setError("Duración inválida (segundos, número positivo).");
        return;
      }
      dur = n;
    }
    setBusy(true);
    setError(null);
    try {
      const p = await patchSong(id, {
        title: title.trim() || null,
        artist: artist.trim() || null,
        mood: mood.trim() || null,
        language: language.trim() || null,
        lyrics_text: lyrics.trim() || null,
        lyrics_rights_confirmed: lyricsRights,
        pacing_profile: pacing || null,
        target_duration_seconds: dur,
      });
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar");
    } finally {
      setBusy(false);
    }
  }

  async function runVisionIa() {
    if (!Number.isFinite(id) || !visionBrief.trim()) {
      setError("Escribe al menos una frase sobre cómo imaginas el videoclip.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await applyOnboardingBrief(id, { brief: visionBrief.trim(), mode: iaMode });
      setData(r.project);
      setLastHint(r.hint);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar dirección");
    } finally {
      setBusy(false);
    }
  }

  async function runSectionsIa() {
    if (!Number.isFinite(id)) return;
    setBusy(true);
    setError(null);
    try {
      const p = await applyOnboardingSections(id);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron crear secciones");
    } finally {
      setBusy(false);
    }
  }

  async function runIdeasIa() {
    if (!Number.isFinite(id)) return;
    setBusy(true);
    setError(null);
    try {
      await generateLyricInsights(id, { mode: "auto", replace: true });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron generar ideas");
    } finally {
      setBusy(false);
    }
  }

  async function runLock() {
    if (!Number.isFinite(id)) return;
    setBusy(true);
    setError(null);
    try {
      const p = await lockCreative(id);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo bloquear");
    } finally {
      setBusy(false);
    }
  }

  async function runUnlock() {
    if (!Number.isFinite(id)) return;
    setBusy(true);
    setError(null);
    try {
      const p = await unlockCreative(id);
      setData(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo desbloquear");
    } finally {
      setBusy(false);
    }
  }

  async function runEnqueue() {
    if (!Number.isFinite(id)) return;
    setStubMsg(null);
    setError(null);
    try {
      const r = await enqueueAnalysis(id);
      const rec =
        (r.recommendations?.length ?? 0) > 0
          ? `\n\nSiguientes pasos:\n${(r.recommendations ?? []).map((x) => `· ${x}`).join("\n")}`
          : "";
      setStubMsg(`${r.status}: ${r.message}${rec}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gate no superado");
    }
  }

  async function peekDocs() {
    if (!Number.isFinite(id)) return;
    setBusy(true);
    setError(null);
    try {
      const d = await getDocumentsPreview(id);
      const clip = d.visual_bible_markdown.slice(0, 1200);
      setDocPeek(clip + (d.visual_bible_markdown.length > 1200 ? "\n\n…" : ""));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar preview");
    } finally {
      setBusy(false);
    }
  }

  function canGoStep1Next() {
    return lyrics.trim().length > 0 && lyricsRights;
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
          Volver
        </Link>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-8 pb-16">
      <div>
        <p className="text-xs uppercase tracking-wide text-[var(--vz-muted)]">Onboarding guiado</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">{data.name}</h1>
        <p className="mt-2 text-sm text-[var(--vz-muted)]">
          Flujo en pocos pasos. La IA rellena dirección, planos sugeridos y plan de export — sin pegar JSON.
        </p>
      </div>

      {locked ? (
        <p className="rounded-lg border border-amber-800/50 bg-amber-950/25 px-3 py-2 text-sm text-amber-200">
          Dirección bloqueada. Puedes exportar y revisar documentos; usa &quot;Desbloquear&quot; al final para seguir
          editando.
        </p>
      ) : null}

      <div className="flex flex-wrap gap-1">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            disabled={busy}
            onClick={() => setStep(i)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              step === i ? "bg-[var(--vz-accent)] text-white" : "bg-[var(--vz-card)] text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      {step === 0 ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-lg font-semibold text-zinc-100">Te guiamos desde la letra</h2>
          <ul className="list-inside list-disc space-y-2 text-sm text-zinc-300">
            <li>Paso 1: letra + datos mínimos (y confirmación de derechos).</li>
            <li>Paso 2: describes el videoclip en lenguaje natural; la IA rellena dirección y planos base.</li>
            <li>Paso 3: IA propone secciones de letra y sugerencias visuales.</li>
            <li>Paso 4: bloqueo creativo y enlaces de export.</li>
          </ul>
          <button
            type="button"
            className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            onClick={() => setStep(1)}
          >
            Empezar
          </button>
        </section>
      ) : null}

      {step === 1 ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-lg font-semibold text-zinc-100">Letra y canción</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Título" htmlFor="g-title">
              <input id="g-title" className="vz-input" value={title} disabled={locked} onChange={(e) => setTitle(e.target.value)} />
            </Field>
            <Field label="Artista" htmlFor="g-artist">
              <input id="g-artist" className="vz-input" value={artist} disabled={locked} onChange={(e) => setArtist(e.target.value)} />
            </Field>
            <Field label="Mood (opcional)" htmlFor="g-mood">
              <input id="g-mood" className="vz-input" value={mood} disabled={locked} onChange={(e) => setMood(e.target.value)} />
            </Field>
            <Field label="Idioma (opcional)" htmlFor="g-lang">
              <input id="g-lang" className="vz-input" value={language} disabled={locked} onChange={(e) => setLanguage(e.target.value)} />
            </Field>
          </div>
          <Field label="Letra" htmlFor="g-lyrics">
            <textarea
              id="g-lyrics"
              className="vz-input min-h-[180px] font-mono text-sm"
              value={lyrics}
              disabled={locked}
              onChange={(e) => setLyrics(e.target.value)}
              placeholder="Pega la letra aquí…"
            />
          </Field>
          <Field label="Duración objetivo / seg (opcional)" htmlFor="g-dur">
            <input id="g-dur" className="vz-input max-w-xs" value={duration} disabled={locked} onChange={(e) => setDuration(e.target.value)} />
          </Field>
          <div>
            <label className="block text-sm font-medium text-zinc-200" htmlFor="g-pacing">
              Pacing
            </label>
            <select id="g-pacing" className="vz-input max-w-md" value={pacing} disabled={locked} onChange={(e) => setPacing(e.target.value)}>
              <option value="">Sin definir</option>
              <option value="slow_cinematic">Lento / cinematográfico</option>
              <option value="balanced">Equilibrado</option>
              <option value="fast_intense">Rápido / intenso</option>
              <option value="minimal">Mínimo / aire</option>
            </select>
          </div>
          <label className="flex cursor-pointer items-start gap-3 text-sm text-zinc-300">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-[var(--vz-border)]"
              checked={lyricsRights}
              disabled={locked}
              onChange={(e) => setLyricsRights(e.target.checked)}
            />
            <span>Confirmo que puedo usar esta letra en este proyecto (derechos / autoría propia).</span>
          </label>
          <details className="rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 text-sm text-zinc-400">
            <summary className="cursor-pointer text-zinc-300">Audio opcional</summary>
            <input
              type="file"
              accept="audio/*"
              disabled={locked || busy}
              className="mt-2 text-xs"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                setBusy(true);
                void uploadAudio(id, f)
                  .then((p) => setData(p))
                  .catch((err) => setError(err instanceof Error ? err.message : "Error subiendo audio"))
                  .finally(() => setBusy(false));
              }}
            />
            {data.song?.has_audio ? (
              <p className="mt-2 text-emerald-400/90">Archivo: {data.song.audio_original_filename}</p>
            ) : null}
          </details>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy || locked}
              onClick={() => void saveBasics()}
              className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white hover:bg-zinc-600 disabled:opacity-50"
            >
              Guardar
            </button>
            <button type="button" className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300" onClick={() => setStep(0)}>
              Atrás
            </button>
            <button
              type="button"
              disabled={!canGoStep1Next() || locked}
              onClick={() => setStep(2)}
              className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
            >
              Continuar
            </button>
          </div>
          {lines.length > 0 ? (
            <div>
              <p className="text-xs font-medium text-zinc-500">Vista previa de líneas</p>
              <div className="mt-1 max-h-32 overflow-y-auto rounded border border-[var(--vz-border)] p-2 font-mono text-xs text-zinc-400">
                {lines.map((l) => (
                  <div key={l.index}>
                    {l.index}: {l.text || "·"}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {step === 2 ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-lg font-semibold text-zinc-100">Tu visión (lenguaje natural)</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            Escribe como si se lo contaras a un director: luces, espacios, sensación, ritmo. No hace falta técnica
            cinematográfica.
          </p>
          <textarea
            className="vz-input min-h-[160px] text-sm"
            value={visionBrief}
            disabled={locked}
            onChange={(e) => setVisionBrief(e.target.value)}
            placeholder="Ej.: Noche lluviosa, neón en charcos, mucho silencio visual, protagonista solo en el coche mirando el retrovisor…"
          />
          <div className="space-y-2">
            <p className="text-xs font-medium text-zinc-500">Motor</p>
            <div className="flex flex-wrap gap-3 text-sm text-zinc-300">
              <label className="flex items-center gap-2">
                <input type="radio" name="iam" checked={iaMode === "auto"} onChange={() => setIaMode("auto")} />
                Auto (OpenAI si hay clave; si no, heurística)
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="iam" checked={iaMode === "heuristic"} onChange={() => setIaMode("heuristic")} />
                Solo heurística local
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="iam" checked={iaMode === "llm"} onChange={() => setIaMode("llm")} />
                OpenAI (requiere clave)
              </label>
            </div>
          </div>
          <button
            type="button"
            disabled={busy || locked || !visionBrief.trim()}
            onClick={() => void runVisionIa()}
            className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            Generar dirección y plan base con IA
          </button>
          {lastHint ? <p className="text-sm text-emerald-400/90">{lastHint}</p> : null}
          {intakePreview ? (
            <div className="rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 text-xs text-zinc-400">
              <span className="font-medium text-zinc-500">Notas guardadas (extracto): </span>
              {intakePreview}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300" onClick={() => setStep(1)}>
              Atrás
            </button>
            <button type="button" className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white" onClick={() => setStep(3)}>
              Continuar
            </button>
          </div>
        </section>
      ) : null}

      {step === 3 ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-lg font-semibold text-zinc-100">Estructura e ideas</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            Primero secciones (por estrofas separadas por línea en blanco en la letra). Luego ideas visuales sugeridas.
          </p>
          {warns.length > 0 ? (
            <ul className="list-inside list-disc rounded-lg border border-amber-800/50 bg-amber-950/20 p-2 text-sm text-amber-200">
              {warns.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          ) : null}
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              disabled={busy || locked}
              onClick={() => void runSectionsIa()}
              className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white hover:bg-zinc-600 disabled:opacity-50"
            >
              Sugerir secciones con IA
            </button>
            <button
              type="button"
              disabled={busy || locked}
              onClick={() => void runIdeasIa()}
              className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white hover:bg-zinc-600 disabled:opacity-50"
            >
              Generar ideas visuales
            </button>
          </div>
          <p className="text-xs text-zinc-500">
            Secciones: {nSec} · Ideas: {nIns}
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300" onClick={() => setStep(2)}>
              Atrás
            </button>
            <button type="button" className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white" onClick={() => setStep(4)}>
              Continuar
            </button>
          </div>
        </section>
      ) : null}

      {step === 4 ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-lg font-semibold text-zinc-100">Cerrar y exportar</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            Cuando no haya avisos de estructura y tengas derechos de letra, bloquea la dirección. Luego descarga
            Markdown / JSON / CSV.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy || locked}
              onClick={() => void runLock()}
              className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
            >
              Bloquear dirección (Creative Lock)
            </button>
            <button
              type="button"
              disabled={busy || !locked}
              onClick={() => void runUnlock()}
              className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300 disabled:opacity-40"
            >
              Desbloquear
            </button>
            <button type="button" disabled={busy} onClick={() => void peekDocs()} className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300">
              Ver extracto Visual Bible
            </button>
            <button type="button" onClick={() => void runEnqueue()} className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300">
              Comprobar gate (stub)
            </button>
          </div>
          {docPeek ? (
            <pre className="max-h-56 overflow-auto whitespace-pre-wrap rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 text-xs text-zinc-400">
              {docPeek}
            </pre>
          ) : null}
          {stubMsg ? <p className="whitespace-pre-wrap text-sm text-emerald-400/90">{stubMsg}</p> : null}
          <p className="text-xs font-medium text-zinc-500">Export (abre en pestaña nueva)</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-[var(--vz-accent)]">
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/bundle.md`} target="_blank" rel="noreferrer">
                bundle.md
              </a>
            </li>
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/shots.json`} target="_blank" rel="noreferrer">
                shots.json
              </a>
            </li>
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/shots.csv`} target="_blank" rel="noreferrer">
                shots.csv
              </a>
            </li>
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/prompts.md?provider=runway`} target="_blank" rel="noreferrer">
                prompts (Runway)
              </a>
            </li>
          </ul>
          <button type="button" className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-300" onClick={() => setStep(3)}>
            Atrás
          </button>
        </section>
      ) : null}

      <Link href="/" className="inline-block text-sm text-[var(--vz-muted)] hover:text-white">
        ← Inicio
      </Link>
    </div>
  );
}
