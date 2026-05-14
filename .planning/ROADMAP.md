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

## Progress

**Execution Order:** 1 → 1.5 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & monorepo shell | 3/3 | Complete | 2026-05-13 |
| 1.5 Lyrics-first alignment | 3/3 | Complete | 2026-05-13 |
| 2. Lyric structure & intelligence | MVP | Complete (code) | 2026-05-13 |
| 3. Optional timing & creative direction | MVP | Complete (code) | 2026-05-13 |
| 4. Visual bible & treatment | MVP | Complete (code) | 2026-05-13 |
| 5. Timeline, scenes & shot list | MVP (JSON) | Complete (code) | 2026-05-13 |
| 6. Prompt compile & export bundle | MVP | Complete (code) | 2026-05-13 |
