# Roadmap: VideoZero (v1 · letra primero)

## Overview

Construir VideoZero como **director creativo guiado por la letra**: el MVP demuestra valor **sin audio obligatorio**, con **estructura de letra**, **dirección guiada**, **Creative Lock**, documentos (biblia + treatment), timeline anclada a **secciones de letra**, shot list y prompt packs exportables. El modo **Audio Pro** (DSP, BPM, onsets, curvas) queda explícitamente fuera del camino crítico hasta v2.

## Phases

- [x] **Phase 1: Foundation & monorepo shell** — Repo ejecutable, proyecto, ingest inicial (hoy incluye audio opcional + gates legacy)
- [x] **Phase 1.5: Lyrics-first alignment** — Gates, copy y modelo alineados con “letra obligatoria”, OPS separado, reloj por duración objetivo
- [x] **Phase 2: Lyric structure & intelligence** — Secciones vinculadas a letra, pacing guiado, parsing + análisis LLM de letra (MVP en repo)
- [x] **Phase 3: Optional timing & creative direction** — Campos JSON + intake/rutas + Creative Lock (MVP)
- [x] **Phase 4: Visual bible & treatment** — Preview Markdown + plantillas (MVP)
- [x] **Phase 5: Timeline, scenes & shot list** — Campos `timeline_plan_json` / `scenes_json` / `shots_json` + UI JSON (editor visual dedicado → backlog)
- [x] **Phase 6: Prompt compile, generation plan & export bundle** — Compile + bundle.md + prompts + shots.json/csv (MVP)

### Milestone v2 — Render & Direction (URL/letra → vídeo final)

- [x] **Phase 7: Audio ingest & lyric alignment (F1)** — yt-dlp + Demucs + WhisperX + librosa → line_timings + BPM/beats (local)
- [x] **Phase 8: Music-driven timeline planner (F2)** — cortes anclados a tiempos reales de letra + snap a beat + energía
- [x] **Phase 9: Render client & cost gate (F3)** — fal.ai (Kling 3.0) por segmento + estimación + tope de presupuesto (dry-run)
- [x] **Phase 10: Keyframes plan (F4)** — keyframe por segmento, encadenado para continuidad (plan/dry-run)
- [x] **Phase 11: Final assembly + E2E orchestration (F5)** — ffmpeg concat + mux audio original + SRT; `make_video` un comando
- [ ] **Phase 12: Cinematic prompting & direction quality (F6)** — biblia inyectada por capas, shots ricos, modulación por energía, init-image real, tuning por proveedor, reroll dirigido

## Phase Details

### Phase 1: Foundation & monorepo shell

**Goal:** Monorepo Next + FastAPI + persistencia mínima; pantalla inicial de proyecto; ingest temprano (incluye audio opcional heredado de la primera iteración).

**Depends on:** Nothing

**Requirements (original slice):** PROJ-01, PROJ-02, ING-02 (audio path), ING-03, OPS parcial

**Mode:** mvp

**Success Criteria:**

1. Dev puede levantar API + web con README.
2. Crear proyecto y persistir datos básicos.
3. *(Legacy)* Gate de análisis asociado a audio — será reemplazado por **Phase 1.5**.

**Plans:**

- [x] 01-01: Bootstrap monorepo
- [x] 01-02: Modelo proyecto/canción + API + SQLite
- [x] 01-03: UI “setup” inicial + upload opcional

### Phase 1.5: Lyrics-first alignment (INSERTED)

**Goal:** El producto en repo refleja el mantra: **letra obligatoria**, **audio opcional**, **OPS** separado (letra vs audio si hay archivo), **duración objetivo** opcional; el stub de pipeline exige derechos de letra + letra no vacía.

**Depends on:** Phase 1

**Requirements:** ING-01, ING-04, OPS-01, OPS-02 (+ ajustes de ING-02/03 según UI)

**Mode:** mvp

**Success Criteria:**

1. No se puede marcar “listo para pipeline” sin **letra** y sin **OPS-01**.
2. Si hay archivo de audio, **OPS-02** aparece y es obligatorio antes de procesar audio (ffprobe/jobs futuros).
3. El usuario puede fijar **duración objetivo** sin subir audio.

**Plans:**

- [x] 01.5-01: Modelo/API/UI — `target_duration_seconds`, `lyrics_rights_confirmed`, copy OPS
- [x] 01.5-02: Stub `analysis/enqueue` → gate “letra primero” (y audio si aplica)
- [x] 01.5-03: README + strings UI alineados al posicionamiento

### Phase 2: Lyric structure & intelligence

**Goal:** Secciones de letra editables + pacing guiado + pipeline LLM de análisis de letra.

**Depends on:** Phase 1.5

**Requirements:** STR-01, STR-02, LYR-01, LYR-02

**Mode:** mvp

**Success Criteria:**

1. Secciones enlazan a bloques/líneas y se reflejan en API.
2. Parsing de letra + sugerencias editables en UI.
3. Pacing elegido condiciona defaults del planner (sin DSP).

**Plans:** MVP shipped in application code (2026-05-13); formal plan files TBD if you re-open the phase for polish.

### Phase 3: Optional timing & creative direction

**Goal:** Tabla de tiempos opcional; intake; cuestionario; rutas; Creative Lock.

**Depends on:** Phase 2

**Requirements:** ALN-01, CRE-01, DIR-01, DIR-02

**Mode:** mvp

**Plans:** MVP (JSON fields + lock endpoints + UI tabs); dedicated timing grid UI → backlog.

### Phase 4: Visual bible & treatment

**Depends on:** Phase 3

**Requirements:** DOC-01, DOC-02

**Mode:** mvp

**Plans:** MVP (`GET …/documents/preview`, exports in bundle).

### Phase 5: Timeline, scenes & shot list

**Depends on:** Phase 4

**Requirements:** PLN-01, PLN-02, PLN-03

**Mode:** mvp

**Plans:** MVP (persisted JSON + Plan tab); visual timeline anchored to sections → backlog.

### Phase 6: Prompt compile, generation plan & export bundle

**Depends on:** Phase 5

**Requirements:** PRM-01, PRM-02, PRM-03, GEN-01, GEN-02, EXP-01, EXP-02, EXP-03

**Mode:** mvp

**Plans:** MVP (`export/bundle.md`, `export/prompts.md`, `export/shots.json`, `export/shots.csv`).

---

## Phase Details — Milestone v2 (Render & Direction)

> Fuente de verdad de diseño v2: [V2-RENDER-PIPELINE.md](V2-RENDER-PIPELINE.md). Estilo del repo:
> stdlib, degradación elegante sin API key, helpers puros testeables, sin imports pesados a nivel
> módulo (CI no instala el extra de audio). Restricción legal: referencias→atributos, nunca copiar
> obra/artista identificable en prompts finales.

### Phase 7: Audio ingest & lyric alignment (F1)

**Goal:** Dada una URL/archivo + letra, producir tiempos reales por línea + BPM/beats/energía (local).
**Depends on:** Phase 6 · **Status:** Complete (code, 2026-05-28)
**Entregables:** `audio_ingest.py`, `music_analysis.py`, `ingest_audio.py`, `requirements-audio.txt`.

### Phase 8: Music-driven timeline planner (F2)

**Goal:** Timeline contiguo anclado a tiempos de letra + snap a beat + troceo por energía; fallback heurístico.
**Depends on:** Phase 7 · **Status:** Complete (code, 2026-05-28)
**Entregables:** `music_planner.py` (`plan_timeline`).

### Phase 9: Render client & cost gate (F3)

**Goal:** Cliente fal.ai (Kling 3.0 default) por segmento + estimación 2026 + tope de presupuesto que aborta antes de gastar.
**Depends on:** Phase 8 · **Status:** Complete (code dry-run, 2026-05-28)
**Entregables:** `render_client.py`, `render_clip.py`.

### Phase 10: Keyframes plan (F4)

**Goal:** Plan de keyframe por segmento, encadenado (referencia el anterior) para continuidad.
**Depends on:** Phase 9 · **Status:** Complete (plan/dry-run, 2026-05-29)
**Entregables:** `keyframes.py`.

### Phase 11: Final assembly + E2E orchestration (F5)

**Goal:** Ensamblado ffmpeg (concat + mux audio original + SRT) y orquestador `make_video` de un comando.
**Depends on:** Phase 10 · **Status:** Complete (code dry-run/local, 2026-05-29)
**Entregables:** `video_assembly.py`, `assemble_video.py`, `pipeline.py`, `make_video.py`.

### Phase 12: Cinematic prompting & direction quality (F6)

**Goal:** Elevar la CALIDAD de la dirección y el prompting para que el videoclip resultante sea
coherente y de aspecto profesional, no un collage genérico — manteniendo todo en dry-run (lógica de
texto, sin gasto) salvo el render final.

**Depends on:** Phase 11

**Requirements:** DIRQ-01, DIRQ-02, DIRQ-03, DIRQ-04, DIRQ-05, DIRQ-06, DIRQ-07

**Mode:** standard

**Success Criteria:**

1. **Biblia visual estructurada** (sujeto, mundo, paleta, óptica, regla de luz, grano/DOF,
   referencias→atributos) generada con system-prompt LLM y fallback heurístico, persistida y
   **reutilizada en todos los segmentos**.
2. **Prompt por capas**: cada prompt de segmento incluye, de forma verificable,
   `[sujeto+acción de la línea] + [cámara/movimiento] + [biblia] + [negativos] + [aspect/duración]`
   (test: la biblia aparece en cada prompt; hay bloque de negativos; hay aspect).
3. **Shots ricos por defecto**: 8–15 planos con intención narrativa por sección (no 2), sin key.
4. **Modulación por energía/beat**: tipo de plano y movimiento de cámara escalan con la curva de
   energía de F1/F2 (estribillo = más movimiento; intro/puente = sostenido).
5. **Keyframe encadenado real**: el último frame del clip anterior se pasa como init-image al
   image-to-video del siguiente (camino real aislado; plan verificable en dry-run).
6. **Tuning por proveedor**: estructura/vocabulario de prompt óptimos por motor (Kling vs Veo vs Runway).
7. **Reroll dirigido**: regenerar solo los segmentos marcados, no todo el timeline.
8. **No regresión**: suite sigue verde, sin imports pesados a nivel módulo, degradación sin key.

**Plans:** TBD (este `/gsd-plan-phase 12`).

## Progress

**Execution Order:** 1 → 1.5 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & monorepo shell | 3/3 | Complete | 2026-05-13 |
| 1.5 Lyrics-first alignment | 3/3 | Complete | 2026-05-13 |
| 2. Lyric structure & intelligence | MVP | Complete (code) | 2026-05-13 |
| 3. Optional timing & creative direction | MVP | Complete (code) | 2026-05-13 |
| 4. Visual bible & treatment | MVP | Complete (code) | 2026-05-13 |
| 5. Timeline, scenes & shot list | MVP (JSON) | Complete (code) | 2026-05-13 |
| 6. Prompt compile & export bundle | MVP | Complete (code) | 2026-05-13 |
| 7. Audio ingest & alignment (F1) | code | Complete | 2026-05-28 |
| 8. Music-driven planner (F2) | code | Complete | 2026-05-28 |
| 9. Render client & cost gate (F3) | code | Complete (dry-run) | 2026-05-28 |
| 10. Keyframes plan (F4) | code | Complete (dry-run) | 2026-05-29 |
| 11. Final assembly + E2E (F5) | code | Complete (dry-run) | 2026-05-29 |
| 12. Cinematic prompting & direction (F6) | — | **Planning** | — |
