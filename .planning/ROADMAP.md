# Roadmap: VideoZero

## Overview

Construir VideoZero como **slice vertical** repetible: desde proyecto + ingest hasta export de treatment, biblia, timeline, shot list y prompt packs, con análisis asíncrono de audio y flujo guiado de dirección. Las fases siguen el modelo de datos y el pipeline de [docs/VIDEOZERO-MASTER.md](../docs/VIDEOZERO-MASTER.md); la integración con APIs de render de vídeo queda fuera de v1.

## Phases

- [ ] **Phase 1: Foundation & vertical slice shell** — Monorepo, app shell, proyecto, ingest básico, gate legal audio
- [ ] **Phase 2: Audio & lyrics analysis** — Jobs async, resultados estructurados, UI de revisión
- [ ] **Phase 3: Alignment & creative direction** — Tabla letra–tiempo, intake creativo, cuestionario director, Creative Lock
- [ ] **Phase 4: Visual bible & treatment** — Documentos generados y preview/export Markdown
- [ ] **Phase 5: Timeline, scenes & shot list** — Planificación editable en tablas
- [ ] **Phase 6: Prompt compile, generation plan & export bundle** — Adaptadores Runway/Kling + checklist + paquete de export

## Phase Details

### Phase 1: Foundation & vertical slice shell

**Goal:** Repositorio ejecutable (frontend + API), persistencia mínima de proyecto, subida de audio y letra, metadata, y confirmación de derechos antes de análisis pesado.

**Depends on:** Nothing (first phase)

**Requirements:** PROJ-01, PROJ-02, ING-01, ING-02, ING-03, OPS-01

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. Un desarrollador puede levantar frontend y API con instrucciones en README y ver health checks OK.
2. El usuario puede crear un proyecto, adjuntar audio y letra, rellenar metadata y guardar; al recargar, los datos siguen ahí.
3. Sin marcar la confirmación de derechos del audio, no se encola análisis pesado (comportamiento observable en API o UI).

**Plans:** TBD (refinar en `/gsd-plan-phase 1`)

Plans:

- [ ] 01-01: Bootstrap monorepo (Next.js + FastAPI), lint/format mínimo, variables de entorno
- [ ] 01-02: Modelo de datos proyecto/canción + API REST + SQLite
- [ ] 01-03: UI shell: pasos “Song Setup” + upload + formulario metadata + checkbox OPS-01

### Phase 2: Audio & lyrics analysis

**Goal:** Pipeline de análisis de audio (librosa/ffmpeg) y análisis de letra (LLM o pipeline inicial) con progreso y resultados consultables.

**Depends on:** Phase 1

**Requirements:** ANA-01, ANA-02, ANA-03, LYR-01, LYR-02

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. Tras upload válido y confirmación OPS-01, se lanza job async y la UI muestra progreso hasta completado o error.
2. Los resultados incluyen duración, BPM aproximado, segmentos tentativos y curva de energía accesibles vía API/UI.
3. La letra queda en líneas/blocks ordenados y el usuario puede corregir el parseo básico en UI si aplica.

**Plans:** TBD

Plans:

- [ ] 02-01: Worker + cola + endpoint de job + SSE/WebSocket de progreso
- [ ] 02-02: Integración librosa/ffmpeg y persistencia de features
- [ ] 02-03: Pipeline letra + prompts versionados en `/prompts` (repo) para extracción de motifs

### Phase 3: Alignment & creative direction

**Goal:** Tabla editable letra–tiempo; intake de referencias traducido a atributos; cuestionario de director; rutas creativas y **Creative Lock** versionado.

**Depends on:** Phase 2

**Requirements:** ALN-01, CRE-01, DIR-01, DIR-02

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. El usuario puede ajustar start/end por línea y ver preview temporal simple (o números validados) sin romper el modelo.
2. Las respuestas del cuestionario y del intake quedan persistidas y alimentan constraints versionados.
3. Hasta que no exista “lock”, la fase de generación masiva de planos no está disponible (gating claro en UI o API).

**Plans:** TBD

Plans:

- [ ] 03-01: UI tabla alineación + validación de solapes / orden
- [ ] 03-02: Persistencia CreativeSession + motor de preguntas (config-driven)
- [ ] 03-03: Rutas creativas + acción “Lock direction” con snapshot

### Phase 4: Visual bible & treatment

**Goal:** Generar Visual Bible y Treatment exportables desde el lock y datos estructurados.

**Depends on:** Phase 3

**Requirements:** DOC-01, DOC-02

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. Con un proyecto de demo bloqueado, el sistema produce Markdown de biblia y treatment coherentes con las respuestas guardadas.
2. El usuario puede previsualizar y editar texto en UI antes de marcar como “final para export” (versión ligera).

**Plans:** TBD

Plans:

- [ ] 04-01: Schemas de salida + prompts `visual_bible` / `treatment`
- [ ] 04-02: UI preview Markdown + diff vs última versión

### Phase 5: Timeline, scenes & shot list

**Goal:** Timeline por secciones, scene cards y shot list derivados y editables en tablas.

**Depends on:** Phase 4

**Requirements:** PLN-01, PLN-02, PLN-03

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. Cada bloque de timeline referencia líneas/letra y secciones musicales de forma trazable.
2. Escenas enlazan bloques y referencias a biblia (localización/personajes).
3. Shot list editable: timestamps, cámara, acción, continuidad, criterios de revisión visibles por fila.

**Plans:** TBD

Plans:

- [ ] 05-01: Timeline planner (LLM o reglas) + UI bloques
- [ ] 05-02: Scene planner + vínculos
- [ ] 05-03: Shot list generator + grid edit

### Phase 6: Prompt compile, generation plan & export bundle

**Goal:** Compilador genérico + Runway + Kling; plan de generación; checklist y matriz; export Markdown/CSV/JSON/prompt packs.

**Depends on:** Phase 5

**Requirements:** PRM-01, PRM-02, PRM-03, GEN-01, GEN-02, EXP-01, EXP-02, EXP-03

**Mode:** mvp

**Success Criteria** (what must be TRUE):

1. Para cada shot, existen al menos tres salidas de texto: generic, Runway, Kling, derivadas del mismo canon interno.
2. El usuario obtiene generation plan + checklist + CSV de revisión descargables.
3. Un “Export bundle” descarga o lista archivos coherentes con los nombres acordados en el master doc §12.

**Plans:** TBD

Plans:

- [ ] 06-01: `ShotPromptInput` canónico + perfiles proveedor
- [ ] 06-02: Generation plan + checklist + review matrix export
- [ ] 06-03: Zip o carpeta de export unificada + prueba E2E con canción demo

## Progress

**Execution Order:** Phases 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & vertical slice shell | 0/TBD | Not started | - |
| 2. Audio & lyrics analysis | 0/TBD | Not started | - |
| 3. Alignment & creative direction | 0/TBD | Not started | - |
| 4. Visual bible & treatment | 0/TBD | Not started | - |
| 5. Timeline, scenes & shot list | 0/TBD | Not started | - |
| 6. Prompt compile & export bundle | 0/TBD | Not started | - |
