"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { LyricInsight, LyricSection, ProjectDetail } from "@/lib/api";
import {
  API_BASE,
  createLyricInsight,
  createLyricSection,
  deleteLyricInsight,
  deleteLyricSection,
  enqueueAnalysis,
  generateLyricInsights,
  getDocumentsPreview,
  getLyricLines,
  getProject,
  lockCreative,
  patchLyricInsight,
  patchLyricSection,
  patchSong,
  reorderLyricInsights,
  reorderLyricSections,
  unlockCreative,
  uploadAudio,
} from "@/lib/api";

const INSIGHT_CATEGORIES: { value: string; label: string }[] = [
  { value: "motif", label: "Motivo / imagen" },
  { value: "symbol", label: "Símbolo" },
  { value: "place", label: "Lugar" },
  { value: "hook", label: "Gancho interpretativo" },
];

const SECTION_KINDS: { value: string; label: string }[] = [
  { value: "intro", label: "Intro" },
  { value: "verse", label: "Verso" },
  { value: "chorus", label: "Estribillo" },
  { value: "bridge", label: "Puente" },
  { value: "hook", label: "Hook" },
  { value: "outro", label: "Outro" },
  { value: "custom", label: "Personalizado" },
];

export default function ProjectLyricSetupPage() {
  const params = useParams();
  const id = Number(params.id);
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [stubMsg, setStubMsg] = useState<string | null>(null);
  const [lines, setLines] = useState<{ index: number; text: string }[]>([]);
  const [newSec, setNewSec] = useState({ label: "", kind: "verse", start: "0", end: "0" });
  const [insightMode, setInsightMode] = useState<"auto" | "heuristic" | "llm">("auto");
  const [insightReplace, setInsightReplace] = useState(true);
  const [insightNote, setInsightNote] = useState<string | null>(null);
  const [newInsight, setNewInsight] = useState({ category: "motif", text: "" });
  type WorkspaceTab = "setup" | "direccion" | "plan" | "export";
  const [tab, setTab] = useState<WorkspaceTab>("setup");
  const [docPreview, setDocPreview] = useState<{ vb: string; tr: string } | null>(null);

  const title = data?.song?.title ?? "";
  const artist = data?.song?.artist ?? "";
  const language = data?.song?.language ?? "";
  const mood = data?.song?.mood ?? "";
  const lyrics = data?.song?.lyrics_text ?? "";
  const lyricsRights = data?.song?.lyrics_rights_confirmed ?? false;
  const audioRights = data?.song?.audio_rights_confirmed ?? false;
  const targetDuration =
    data?.song?.target_duration_seconds != null ? String(data.song.target_duration_seconds) : "";

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

  useEffect(() => {
    if (!Number.isFinite(id) || !data?.song) return;
    let cancelled = false;
    void getLyricLines(id)
      .then((r) => {
        if (!cancelled) setLines(r.lines);
      })
      .catch(() => {
        if (!cancelled) setLines([]);
      });
    return () => {
      cancelled = true;
    };
  }, [id, data?.song]);

  const sortedSections = useMemo(
    () => [...(data?.song?.sections ?? [])].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id),
    [data?.song?.sections],
  );

  const sortedInsights = useMemo(
    () => [...(data?.song?.insights ?? [])].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id),
    [data?.song?.insights],
  );

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
      const rec =
        (r.recommendations?.length ?? 0) > 0
          ? `\n\nSiguientes pasos sugeridos:\n${(r.recommendations ?? []).map((x) => `· ${x}`).join("\n")}`
          : "";
      setStubMsg(`${r.status}: ${r.message}${rec}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo encolar");
    }
  }

  async function addNewSection() {
    if (!Number.isFinite(id)) return;
    const label = newSec.label.trim();
    if (!label) {
      setError("El nombre de la sección es obligatorio.");
      return;
    }
    const si = Number.parseInt(newSec.start, 10);
    const ei = Number.parseInt(newSec.end, 10);
    if (!Number.isFinite(si) || !Number.isFinite(ei)) {
      setError("Los índices de línea deben ser números enteros.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createLyricSection(id, {
        label,
        kind: newSec.kind,
        start_line_index: si,
        end_line_index: ei,
      });
      const maxIdx = Math.max(0, lines.length - 1);
      await load();
      setNewSec({ label: "", kind: newSec.kind, start: "0", end: String(maxIdx) });
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo crear la sección");
    } finally {
      setSaving(false);
    }
  }

  async function runInsightGenerate() {
    if (!Number.isFinite(id)) return;
    setSaving(true);
    setError(null);
    setInsightNote(null);
    try {
      const r = await generateLyricInsights(id, { mode: insightMode, replace: insightReplace });
      setInsightNote(
        `Creadas: ${r.created_count} · motor: ${r.engine}${r.note ? ` — ${r.note}` : ""}`,
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron generar ideas");
    } finally {
      setSaving(false);
    }
  }

  async function addManualInsight() {
    if (!Number.isFinite(id)) return;
    const text = newInsight.text.trim();
    if (!text) {
      setError("El texto de la idea es obligatorio.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createLyricInsight(id, { category: newInsight.category, text });
      setNewInsight((s) => ({ ...s, text: "" }));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo añadir la idea");
    } finally {
      setSaving(false);
    }
  }

  async function moveSection(fromIndex: number, delta: -1 | 1) {
    if (!Number.isFinite(id) || !data?.song) return;
    const sorted = [...(data.song.sections ?? [])].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
    const to = fromIndex + delta;
    if (to < 0 || to >= sorted.length) return;
    const next = [...sorted];
    [next[fromIndex], next[to]] = [next[to], next[fromIndex]];
    setSaving(true);
    setError(null);
    try {
      await reorderLyricSections(
        id,
        next.map((s) => s.id),
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo reordenar");
    } finally {
      setSaving(false);
    }
  }

  async function moveInsight(fromIndex: number, delta: -1 | 1) {
    if (!Number.isFinite(id) || !data?.song) return;
    const sorted = [...(data.song.insights ?? [])].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
    const to = fromIndex + delta;
    if (to < 0 || to >= sorted.length) return;
    const next = [...sorted];
    [next[fromIndex], next[to]] = [next[to], next[fromIndex]];
    setSaving(true);
    setError(null);
    try {
      await reorderLyricInsights(
        id,
        next.map((x) => x.id),
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo reordenar");
    } finally {
      setSaving(false);
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

  const locked = data.song?.creative_locked ?? false;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-[var(--vz-muted)]">Letra primero</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">{data.name}</h1>
        <p className="mt-2 text-sm text-[var(--vz-muted)]">
          VideoZero es un <strong className="text-zinc-200">director creativo guiado por la letra</strong>. La pista es
          opcional: sirve como referencia o para afinar tiempo más adelante. El reloj principal del MVP puede ser la{" "}
          <strong className="text-zinc-200">duración objetivo</strong> que indiques.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-[var(--vz-border)] pb-3">
        {(
          [
            ["setup", "Setup · letra"],
            ["direccion", "Dirección"],
            ["plan", "Plan JSON"],
            ["export", "Export"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setTab(key);
              if (key !== "direccion") setDocPreview(null);
            }}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === key
                ? "bg-[var(--vz-accent)] text-white"
                : "bg-[var(--vz-card)] text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {locked ? (
        <p className="rounded-lg border border-amber-800/50 bg-amber-950/25 px-3 py-2 text-sm text-amber-200">
          Creative Lock activo: letra, secciones, ideas y campos de plan están congelados. Usa Dirección → Desbloquear
          para seguir editando.
        </p>
      ) : null}

      {tab === "setup" ? (
        <>
      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Letra y metadata</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Título" htmlFor="f-title">
            <input
              className="vz-input"
              defaultValue={title}
              key={`title-${data.song?.updated_at}`}
              id="f-title"
              readOnly={locked}
            />
          </Field>
          <Field label="Artista" htmlFor="f-artist">
            <input className="vz-input" defaultValue={artist} key={`artist-${data.song?.updated_at}`} id="f-artist" readOnly={locked} />
          </Field>
          <Field label="Idioma (ISO o libre)" htmlFor="f-lang">
            <input className="vz-input" defaultValue={language} key={`lang-${data.song?.updated_at}`} id="f-lang" readOnly={locked} />
          </Field>
          <Field label="Mood objetivo" htmlFor="f-mood">
            <input className="vz-input" defaultValue={mood} key={`mood-${data.song?.updated_at}`} id="f-mood" readOnly={locked} />
          </Field>
        </div>
        <Field label="Letra (entrada principal)" htmlFor="f-lyrics">
          <textarea
            className="vz-input min-h-[200px] font-mono text-sm"
            defaultValue={lyrics}
            key={`lyrics-${data.song?.updated_at}`}
            readOnly={locked}
            id="f-lyrics"
            placeholder="Pega la letra aquí…"
          />
        </Field>
        <Field label="Duración objetivo (segundos, opcional)" htmlFor="f-dur">
          <input
            className="vz-input"
            defaultValue={targetDuration}
            key={`dur-${data.song?.updated_at}`}
            id="f-dur"
            readOnly={locked}
            inputMode="decimal"
            placeholder="Ej. 210"
          />
        </Field>
        <button
          type="button"
          disabled={saving || locked}
          onClick={() => {
            const g = (n: string) => (document.getElementById(n) as HTMLInputElement | HTMLTextAreaElement).value;
            const rawDur = g("f-dur").trim();
            let dur: number | null = null;
            if (rawDur) {
              const n = Number.parseFloat(rawDur);
              if (!Number.isFinite(n) || n <= 0) {
                setError("Duración objetivo inválida (usa segundos, número positivo).");
                return;
              }
              dur = n;
            }
            void save({
              title: g("f-title") || null,
              artist: g("f-artist") || null,
              language: g("f-lang") || null,
              mood: g("f-mood") || null,
              lyrics_text: g("f-lyrics") || null,
              target_duration_seconds: dur,
            });
          }}
          className="rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
        >
          {saving ? "Guardando…" : "Guardar letra, metadata y duración"}
        </button>
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Pacing guiado (STR-02)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Condicionará densidad de planos y ritmo de edición por defecto en fases posteriores, sin análisis DSP.
        </p>
        <label className="block text-sm font-medium text-zinc-200" htmlFor="f-pacing">
          Perfil
        </label>
        <select
          id="f-pacing"
          className="vz-input max-w-md"
          value={data.song?.pacing_profile ?? ""}
          disabled={saving || locked}
          onChange={(e) => void save({ pacing_profile: e.target.value ? e.target.value : null })}
        >
          <option value="">Sin perfil definido</option>
          <option value="slow_cinematic">Lento / cinematográfico</option>
          <option value="balanced">Equilibrado</option>
          <option value="fast_intense">Rápido / intenso</option>
          <option value="minimal">Mínimo / aire</option>
        </select>
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Estructura de letra (STR-01 · LYR-01)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Las secciones se anclan a <strong className="text-zinc-200">índices de línea</strong> (0 = primera línea
          guardada). Si editas la letra, revisa que los rangos sigan teniendo sentido.
        </p>
        {(data.song?.structure_warnings ?? []).length > 0 ? (
          <ul className="list-inside list-disc rounded-lg border border-amber-800/60 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">
            {(data.song?.structure_warnings ?? []).map((w, i) => (
              <li key={i} className="marker:text-amber-500">
                {w}
              </li>
            ))}
          </ul>
        ) : null}
        <div>
          <p className="text-sm font-medium text-zinc-200">Vista previa de líneas</p>
          <div className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 font-mono text-xs text-zinc-300">
            {lines.length === 0 ? (
              <p className="text-[var(--vz-muted)]">Sin líneas — guarda una letra no vacía primero.</p>
            ) : (
              lines.map((l) => (
                <div
                  key={l.index}
                  className="flex gap-2 border-b border-[var(--vz-border)]/50 py-0.5 last:border-0"
                >
                  <span className="w-8 shrink-0 text-right text-[var(--vz-muted)]">{l.index}</span>
                  <span className="whitespace-pre-wrap">{l.text.length ? l.text : "·"}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-zinc-200">Secciones</p>
          <p className="text-xs text-[var(--vz-muted)]">
            Usa <strong className="text-zinc-400">Subir</strong> / <strong className="text-zinc-400">Bajar</strong> para
            cambiar el orden de lectura (no altera los índices de línea).
          </p>
          {sortedSections.map((sec, idx) => (
            <SectionRow
              key={sec.id}
              projectId={id}
              section={sec}
              canMoveUp={idx > 0}
              canMoveDown={idx < sortedSections.length - 1}
              reorderBusy={saving}
              readOnly={locked}
              onMoveUp={() => void moveSection(idx, -1)}
              onMoveDown={() => void moveSection(idx, 1)}
              onChanged={() => void load()}
              onError={setError}
            />
          ))}
          {sortedSections.length === 0 ? (
            <p className="text-sm text-[var(--vz-muted)]">Aún no hay secciones. Añade la primera abajo.</p>
          ) : null}
        </div>

        <div className="rounded-lg border border-dashed border-[var(--vz-border)] p-4">
          <p className="text-sm font-medium text-zinc-200">Nueva sección</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Field label="Nombre" htmlFor="ns-label">
              <input
                id="ns-label"
                className="vz-input"
                value={newSec.label}
                disabled={locked}
                onChange={(e) => setNewSec((s) => ({ ...s, label: e.target.value }))}
                placeholder="Ej. Estribillo A"
              />
            </Field>
            <Field label="Tipo" htmlFor="ns-kind">
              <select
                id="ns-kind"
                className="vz-input"
                value={newSec.kind}
                disabled={locked}
                onChange={(e) => setNewSec((s) => ({ ...s, kind: e.target.value }))}
              >
                {SECTION_KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Línea inicio (incl.)" htmlFor="ns-start">
              <input
                id="ns-start"
                className="vz-input"
                inputMode="numeric"
                value={newSec.start}
                disabled={locked}
                onChange={(e) => setNewSec((s) => ({ ...s, start: e.target.value }))}
              />
            </Field>
            <Field label="Línea fin (incl.)" htmlFor="ns-end">
              <input
                id="ns-end"
                className="vz-input"
                inputMode="numeric"
                value={newSec.end}
                disabled={locked}
                onChange={(e) => setNewSec((s) => ({ ...s, end: e.target.value }))}
              />
            </Field>
          </div>
          <button
            type="button"
            disabled={saving || lines.length === 0 || locked}
            onClick={() => void addNewSection()}
            className="mt-4 rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
          >
            {saving ? "Guardando…" : "Añadir sección"}
          </button>
        </div>
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Ideas visuales (LYR-02)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Motivos, símbolos, lugares y ganchos interpretativos. Puedes <strong className="text-zinc-200">generar</strong>{" "}
          (heurística local o, si configuras <code className="text-zinc-400">VIDEOZERO_OPENAI_API_KEY</code>, LLM) y
          luego <strong className="text-zinc-200">editar</strong> cada ítem; al guardar ediciones pasan a origen
          «usuario».
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-zinc-400" htmlFor="ins-mode">
              Motor
            </label>
            <select
              id="ins-mode"
              className="vz-input mt-1 min-w-[11rem]"
              value={insightMode}
              disabled={saving || locked}
              onChange={(e) => setInsightMode(e.target.value as typeof insightMode)}
            >
              <option value="auto">Auto (LLM si hay clave)</option>
              <option value="heuristic">Solo heurística</option>
              <option value="llm">Solo LLM</option>
            </select>
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={insightReplace}
              disabled={saving || locked}
              onChange={(e) => setInsightReplace(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--vz-border)]"
            />
            Reemplazar sugerencias auto (heurística/LLM), conservar manuales
          </label>
          <button
            type="button"
              disabled={saving || !(data.song?.lyrics_text ?? "").trim() || locked}
            onClick={() => void runInsightGenerate()}
            className="rounded-lg bg-[var(--vz-accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Generando…" : "Generar ideas"}
          </button>
        </div>
        {insightNote ? <p className="text-sm text-emerald-400/90">{insightNote}</p> : null}

        <div className="space-y-3">
          <p className="text-sm font-medium text-zinc-200">Ítems</p>
          <p className="text-xs text-[var(--vz-muted)]">
            <strong className="text-zinc-400">Subir</strong> / <strong className="text-zinc-400">Bajar</strong> cambia
            solo el orden de presentación.
          </p>
          {sortedInsights.length === 0 ? (
            <p className="text-sm text-[var(--vz-muted)]">Aún no hay ideas guardadas.</p>
          ) : (
            sortedInsights.map((ins, idx) => (
              <InsightRow
                key={ins.id}
                projectId={id}
                insight={ins}
                canMoveUp={idx > 0}
                canMoveDown={idx < sortedInsights.length - 1}
                reorderBusy={saving}
                readOnly={locked}
                onMoveUp={() => void moveInsight(idx, -1)}
                onMoveDown={() => void moveInsight(idx, 1)}
                onChanged={() => void load()}
                onError={setError}
              />
            ))
          )}
        </div>

        <div className="rounded-lg border border-dashed border-[var(--vz-border)] p-4">
          <p className="text-sm font-medium text-zinc-200">Añadir manualmente</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Field label="Categoría" htmlFor="ni-cat">
              <select
                id="ni-cat"
                className="vz-input"
                value={newInsight.category}
                disabled={locked}
                onChange={(e) => setNewInsight((s) => ({ ...s, category: e.target.value }))}
              >
                {INSIGHT_CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Texto" htmlFor="ni-text">
              <input
                id="ni-text"
                className="vz-input"
                value={newInsight.text}
                disabled={locked}
                onChange={(e) => setNewInsight((s) => ({ ...s, text: e.target.value }))}
                placeholder="Ej. Imagen recurrente del espejo roto"
              />
            </Field>
          </div>
          <button
            type="button"
            disabled={saving || locked}
            onClick={() => void addManualInsight()}
            className="mt-3 rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
          >
            Añadir idea
          </button>
        </div>
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Audio (opcional)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Estado:{" "}
          {data.song?.has_audio ? (
            <span className="text-emerald-400">Archivo cargado ({data.song.audio_original_filename})</span>
          ) : (
            <span className="text-amber-300">Sin archivo — puedes continuar solo con letra.</span>
          )}
        </p>
        <input
          type="file"
          accept="audio/*,.mp3,.wav,.flac,.m4a,.aac,.ogg,.webm"
          disabled={saving || locked}
          onChange={(e) => void onAudioChange(e.target.files?.[0] ?? null)}
          className="text-sm text-[var(--vz-muted)] file:mr-4 file:rounded-lg file:border-0 file:bg-[var(--vz-accent)] file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
        />
      </section>

      <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Derechos (OPS)</h2>
        <label className="flex cursor-pointer items-start gap-3 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={lyricsRights}
            disabled={saving}
            onChange={(e) => void save({ lyrics_rights_confirmed: e.target.checked })}
            className="mt-1 h-4 w-4 rounded border-[var(--vz-border)]"
          />
          <span>
            Confirmo que tengo derecho a usar <strong className="text-zinc-200">esta letra</strong> en este proyecto
            (autoría propia o licencia válida).
          </span>
        </label>
        {data.song?.has_audio ? (
          <label className="flex cursor-pointer items-start gap-3 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={audioRights}
              disabled={saving}
              onChange={(e) => void save({ audio_rights_confirmed: e.target.checked })}
              className="mt-1 h-4 w-4 rounded border-[var(--vz-border)]"
            />
            <span>
              Hay un archivo de audio: confirmo que tengo derecho a usar <strong className="text-zinc-200">esta
              pista</strong> antes de cualquier procesamiento de audio.
            </span>
          </label>
        ) : null}
      </section>

      <section className="space-y-3 rounded-xl border border-dashed border-[var(--vz-border)] bg-[var(--vz-bg)] p-6">
        <h2 className="text-sm font-semibold text-zinc-200">Gate del pipeline (stub)</h2>
        <p className="text-sm text-[var(--vz-muted)]">
          Valida letra + OPS (y audio si aplica). No encola jobs: la respuesta incluye{" "}
          <strong className="text-zinc-200">recomendaciones</strong> para cerrar secciones, ideas, lock y planos antes
          de exportar.
        </p>
        <button
          type="button"
          onClick={() => void tryEnqueue()}
          className="rounded-lg border border-[var(--vz-border)] px-4 py-2 text-sm text-zinc-200 hover:border-[var(--vz-accent)]"
        >
          Probar POST /projects/…/analysis/enqueue
        </button>
        {stubMsg ? (
          <p className="whitespace-pre-wrap text-sm text-emerald-400">{stubMsg}</p>
        ) : null}
      </section>

        </>
      ) : null}

      {tab === "direccion" ? (
        <section className="space-y-6 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-sm font-semibold text-zinc-200">Dirección creativa · lock · documentos</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            JSON válido en cada campo. Con Creative Lock activo no podrás editarlos hasta desbloquear.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={saving || locked}
              onClick={async () => {
                setSaving(true);
                setError(null);
                try {
                  const p = await lockCreative(id);
                  setData(p);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "No se pudo bloquear");
                } finally {
                  setSaving(false);
                }
              }}
              className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600 disabled:opacity-50"
            >
              Bloquear dirección (Creative Lock)
            </button>
            <button
              type="button"
              disabled={saving || !locked}
              onClick={async () => {
                setSaving(true);
                setError(null);
                try {
                  const p = await unlockCreative(id);
                  setData(p);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "No se pudo desbloquear");
                } finally {
                  setSaving(false);
                }
              }}
              className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-200 hover:border-[var(--vz-accent)] disabled:opacity-50"
            >
              Desbloquear
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={async () => {
                setSaving(true);
                setError(null);
                try {
                  const d = await getDocumentsPreview(id);
                  setDocPreview({ vb: d.visual_bible_markdown, tr: d.treatment_markdown });
                } catch (e) {
                  setError(e instanceof Error ? e.message : "No se pudo cargar la vista previa");
                } finally {
                  setSaving(false);
                }
              }}
              className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white hover:bg-zinc-600 disabled:opacity-50"
            >
              Cargar vista previa (Visual Bible + Treatment)
            </button>
          </div>
          {data.song?.creative_lock_at ? (
            <p className="text-xs text-[var(--vz-muted)]">Bloqueado en: {data.song.creative_lock_at}</p>
          ) : null}

          <Field label="Ruta seleccionada (id)" htmlFor="f-route-id">
            <input
              id="f-route-id"
              className="vz-input max-w-md"
              defaultValue={data.song?.selected_route_id ?? ""}
              key={`rid-${data.song?.updated_at}`}
              disabled={saving || locked}
            />
          </Field>
          <button
            type="button"
            disabled={saving || locked}
            onClick={() => {
              const v = (document.getElementById("f-route-id") as HTMLInputElement).value.trim();
              void save({ selected_route_id: v || null });
            }}
            className="rounded-lg bg-zinc-700 px-3 py-1.5 text-sm text-white hover:bg-zinc-600 disabled:opacity-50"
          >
            Guardar ruta seleccionada
          </button>

          <JsonArea
            id="j-intake"
            label="creative_intake_json"
            defaultJson={data.song?.creative_intake_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder='{"reference_notes":"","style_attributes":[]}'
            onSave={(raw) => void save({ creative_intake_json: raw || null })}
          />
          <JsonArea
            id="j-director"
            label="director_answers_json"
            defaultJson={data.song?.director_answers_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder="{}"
            onSave={(raw) => void save({ director_answers_json: raw || null })}
          />
          <JsonArea
            id="j-routes"
            label="creative_routes_json"
            defaultJson={data.song?.creative_routes_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder='{"routes":[{"id":"a","title":"Ruta A","summary":"..."}]}'
            onSave={(raw) => void save({ creative_routes_json: raw || null })}
          />

          {docPreview ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-medium text-zinc-400">Visual Bible</p>
                <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 text-xs text-zinc-300">
                  {docPreview.vb}
                </pre>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-zinc-400">Treatment</p>
                <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-3 text-xs text-zinc-300">
                  {docPreview.tr}
                </pre>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {tab === "plan" ? (
        <section className="space-y-6 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-sm font-semibold text-zinc-200">Planificación (JSON)</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            Timings por línea, planos, plan de generación, etc. Deben ser JSON válidos al guardar.
          </p>
          <JsonArea
            id="j-timings"
            label="line_timings_json"
            defaultJson={data.song?.line_timings_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder="[]"
            onSave={(raw) => void save({ line_timings_json: raw || null })}
          />
          <JsonArea
            id="j-timeline"
            label="timeline_plan_json"
            defaultJson={data.song?.timeline_plan_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder="[]"
            onSave={(raw) => void save({ timeline_plan_json: raw || null })}
          />
          <JsonArea
            id="j-scenes"
            label="scenes_json"
            defaultJson={data.song?.scenes_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder="[]"
            onSave={(raw) => void save({ scenes_json: raw || null })}
          />
          <JsonArea
            id="j-shots"
            label="shots_json"
            defaultJson={data.song?.shots_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder='[{"slug":"s1","camera":"","action":"","notes":""}]'
            onSave={(raw) => void save({ shots_json: raw || null })}
          />
          <JsonArea
            id="j-genplan"
            label="generation_plan_json"
            defaultJson={data.song?.generation_plan_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder='[{"title":"Paso 1","detail":"..."}]'
            onSave={(raw) => void save({ generation_plan_json: raw || null })}
          />
          <JsonArea
            id="j-review"
            label="review_matrix_json"
            defaultJson={data.song?.review_matrix_json}
            updatedAt={data.song?.updated_at}
            disabled={saving || locked}
            placeholder="{}"
            onSave={(raw) => void save({ review_matrix_json: raw || null })}
          />
        </section>
      ) : null}

      {tab === "export" ? (
        <section className="space-y-4 rounded-xl border border-[var(--vz-border)] bg-[var(--vz-card)] p-6">
          <h2 className="text-sm font-semibold text-zinc-200">Export (Markdown, JSON, CSV)</h2>
          <p className="text-sm text-[var(--vz-muted)]">
            Descargas directas contra la API (mismo host que <code className="text-zinc-400">NEXT_PUBLIC_API_URL</code>
            ).
          </p>
          <ul className="list-inside list-disc space-y-2 text-sm text-[var(--vz-accent)]">
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/shots.json`} target="_blank" rel="noreferrer">
                shots.json — lista de planos (desde shots_json)
              </a>
            </li>
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/shots.csv`} target="_blank" rel="noreferrer">
                shots.csv — mismos datos en columnas (slug, camera, action, notes)
              </a>
            </li>
            <li>
              <a className="underline" href={`${API_BASE}/projects/${id}/export/bundle.md`} target="_blank" rel="noreferrer">
                bundle.md — Visual Bible + Treatment + plan + prompts
              </a>
            </li>
            <li>
              <a
                className="underline"
                href={`${API_BASE}/projects/${id}/export/prompts.md?provider=generic`}
                target="_blank"
                rel="noreferrer"
              >
                prompts (genérico)
              </a>
            </li>
            <li>
              <a
                className="underline"
                href={`${API_BASE}/projects/${id}/export/prompts.md?provider=runway`}
                target="_blank"
                rel="noreferrer"
              >
                prompts (runway)
              </a>
            </li>
            <li>
              <a
                className="underline"
                href={`${API_BASE}/projects/${id}/export/prompts.md?provider=kling`}
                target="_blank"
                rel="noreferrer"
              >
                prompts (kling)
              </a>
            </li>
          </ul>
        </section>
      ) : null}

      {error ? <p className="text-sm text-red-400">{error}</p> : null}

      <Link href="/" className="inline-block text-sm text-[var(--vz-muted)] hover:text-white">
        ← Volver al inicio
      </Link>
    </div>
  );
}

function SectionRow({
  projectId,
  section,
  canMoveUp,
  canMoveDown,
  reorderBusy,
  readOnly,
  onMoveUp,
  onMoveDown,
  onChanged,
  onError,
}: {
  projectId: number;
  section: LyricSection;
  canMoveUp: boolean;
  canMoveDown: boolean;
  reorderBusy: boolean;
  readOnly?: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onChanged: () => void | Promise<void>;
  onError: (msg: string | null) => void;
}) {
  const [label, setLabel] = useState(section.label);
  const [kind, setKind] = useState(section.kind);
  const [start, setStart] = useState(String(section.start_line_index));
  const [end, setEnd] = useState(String(section.end_line_index));
  const [busy, setBusy] = useState(false);
  const ro = readOnly ?? false;

  useEffect(() => {
    setLabel(section.label);
    setKind(section.kind);
    setStart(String(section.start_line_index));
    setEnd(String(section.end_line_index));
  }, [section]);

  async function apply() {
    const si = Number.parseInt(start, 10);
    const ei = Number.parseInt(end, 10);
    if (!Number.isFinite(si) || !Number.isFinite(ei)) {
      onError("Los índices de línea deben ser números enteros.");
      return;
    }
    setBusy(true);
    onError(null);
    try {
      await patchLyricSection(projectId, section.id, {
        label: label.trim(),
        kind,
        start_line_index: si,
        end_line_index: ei,
      });
      await onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : "No se pudo actualizar la sección");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    onError(null);
    try {
      await deleteLyricSection(projectId, section.id);
      await onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : "No se pudo eliminar la sección");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Nombre" htmlFor={`sec-${section.id}-label`}>
          <input
            id={`sec-${section.id}-label`}
            className="vz-input"
            value={label}
            readOnly={ro}
            onChange={(e) => setLabel(e.target.value)}
          />
        </Field>
        <Field label="Tipo" htmlFor={`sec-${section.id}-kind`}>
          <select
            id={`sec-${section.id}-kind`}
            className="vz-input"
            value={kind}
            disabled={ro}
            onChange={(e) => setKind(e.target.value)}
          >
            {SECTION_KINDS.map((k) => (
              <option key={k.value} value={k.value}>
                {k.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Inicio" htmlFor={`sec-${section.id}-start`}>
          <input
            id={`sec-${section.id}-start`}
            className="vz-input"
            inputMode="numeric"
            value={start}
            readOnly={ro}
            onChange={(e) => setStart(e.target.value)}
          />
        </Field>
        <Field label="Fin" htmlFor={`sec-${section.id}-end`}>
          <input
            id={`sec-${section.id}-end`}
            className="vz-input"
            inputMode="numeric"
            value={end}
            readOnly={ro}
            onChange={(e) => setEnd(e.target.value)}
          />
        </Field>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          title="Subir"
          disabled={busy || reorderBusy || !canMoveUp || ro}
          onClick={onMoveUp}
          className="rounded-lg border border-[var(--vz-border)] px-2 py-1.5 text-xs text-zinc-200 hover:border-[var(--vz-accent)] disabled:opacity-40"
        >
          ↑
        </button>
        <button
          type="button"
          title="Bajar"
          disabled={busy || reorderBusy || !canMoveDown || ro}
          onClick={onMoveDown}
          className="rounded-lg border border-[var(--vz-border)] px-2 py-1.5 text-xs text-zinc-200 hover:border-[var(--vz-accent)] disabled:opacity-40"
        >
          ↓
        </button>
        <button
          type="button"
          disabled={busy || ro}
          onClick={() => void apply()}
          className="rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
        >
          {busy ? "…" : "Aplicar cambios"}
        </button>
        <button
          type="button"
          disabled={busy || ro}
          onClick={() => void remove()}
          className="rounded-lg border border-red-900/60 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}

function InsightRow({
  projectId,
  insight,
  canMoveUp,
  canMoveDown,
  reorderBusy,
  readOnly,
  onMoveUp,
  onMoveDown,
  onChanged,
  onError,
}: {
  projectId: number;
  insight: LyricInsight;
  canMoveUp: boolean;
  canMoveDown: boolean;
  reorderBusy: boolean;
  readOnly?: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onChanged: () => void | Promise<void>;
  onError: (msg: string | null) => void;
}) {
  const [category, setCategory] = useState(insight.category);
  const [text, setText] = useState(insight.text);
  const [busy, setBusy] = useState(false);
  const ro = readOnly ?? false;

  useEffect(() => {
    setCategory(insight.category);
    setText(insight.text);
  }, [insight]);

  async function apply() {
    const t = text.trim();
    if (!t) {
      onError("El texto no puede quedar vacío.");
      return;
    }
    setBusy(true);
    onError(null);
    try {
      await patchLyricInsight(projectId, insight.id, { category, text: t });
      await onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : "No se pudo actualizar la idea");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    onError(null);
    try {
      await deleteLyricInsight(projectId, insight.id);
      await onChanged();
    } catch (e) {
      onError(e instanceof Error ? e.message : "No se pudo eliminar la idea");
    } finally {
      setBusy(false);
    }
  }

  const srcLabel =
    insight.source === "llm" ? "LLM" : insight.source === "heuristic" ? "Heurística" : "Usuario";

  return (
    <div className="rounded-lg border border-[var(--vz-border)] bg-[var(--vz-bg)] p-4">
      <p className="mb-2 text-xs text-[var(--vz-muted)]">
        Origen: <span className="text-zinc-400">{srcLabel}</span>
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Categoría" htmlFor={`ins-${insight.id}-cat`}>
          <select
            id={`ins-${insight.id}-cat`}
            className="vz-input"
            value={category}
            disabled={ro}
            onChange={(e) => setCategory(e.target.value)}
          >
            {INSIGHT_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Texto" htmlFor={`ins-${insight.id}-text`}>
          <input
            id={`ins-${insight.id}-text`}
            className="vz-input"
            value={text}
            readOnly={ro}
            onChange={(e) => setText(e.target.value)}
          />
        </Field>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          title="Subir"
          disabled={busy || reorderBusy || !canMoveUp || ro}
          onClick={onMoveUp}
          className="rounded-lg border border-[var(--vz-border)] px-2 py-1.5 text-xs text-zinc-200 hover:border-[var(--vz-accent)] disabled:opacity-40"
        >
          ↑
        </button>
        <button
          type="button"
          title="Bajar"
          disabled={busy || reorderBusy || !canMoveDown || ro}
          onClick={onMoveDown}
          className="rounded-lg border border-[var(--vz-border)] px-2 py-1.5 text-xs text-zinc-200 hover:border-[var(--vz-accent)] disabled:opacity-40"
        >
          ↓
        </button>
        <button
          type="button"
          disabled={busy || ro}
          onClick={() => void apply()}
          className="rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
        >
          {busy ? "…" : "Guardar"}
        </button>
        <button
          type="button"
          disabled={busy || ro}
          onClick={() => void remove()}
          className="rounded-lg border border-red-900/60 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}

function JsonArea({
  id,
  label,
  defaultJson,
  updatedAt,
  disabled,
  placeholder,
  onSave,
}: {
  id: string;
  label: string;
  defaultJson?: string | null;
  updatedAt?: string;
  disabled?: boolean;
  placeholder: string;
  onSave: (raw: string) => void;
}) {
  const initial = defaultJson && defaultJson.trim() ? defaultJson : placeholder;
  return (
    <div className="space-y-2">
      <Field label={label} htmlFor={id}>
        <textarea
          id={id}
          key={`${id}-${updatedAt ?? "0"}`}
          className="vz-input min-h-[120px] font-mono text-xs"
          defaultValue={initial}
          disabled={disabled}
          spellCheck={false}
        />
      </Field>
      <button
        type="button"
        disabled={disabled}
        onClick={() => {
          const ta = document.getElementById(id) as HTMLTextAreaElement;
          onSave(ta.value);
        }}
        className="rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-600 disabled:opacity-50"
      >
        Guardar {label}
      </button>
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
