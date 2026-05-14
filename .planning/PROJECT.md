# VideoZero

## What This Is

**VideoZero** es un **director creativo guiado por la letra**: lleva al usuario desde la **letra** (obligatoria) y metadata mínima hasta un **paquete de dirección coherente** para videoclips con IA — interpretación, preguntas de director, rutas creativas, biblia visual, treatment, timeline anclada a **secciones y bloques de letra**, escenas, shot list, prompts por proveedor (compilación, no render unificado), plan de generación y revisión. **El audio es opcional**: refina tiempo y feel cuando existe; **no** define el arranque del flujo ni el valor mínimo del MVP.

**Fuente de verdad de producto:** [docs/VIDEOZERO-MASTER.md](../docs/VIDEOZERO-MASTER.md) (v1 · letra primero).

## Core Value

Que cada plano y cada export **herede** contexto validado anclado en la **letra** y las **decisiones de dirección** (secciones, lock creativo, biblia, continuidad, proveedor objetivo), de modo que el usuario produzca en herramientas externas **sin collage incoherente** — con o sin pista de audio.

## Requirements

### Validated

- [x] **Workspace por proyecto** — Detalle de proyecto + canción persistida; flujo en pestañas (Setup / Dirección / Plan / Export).
- [x] **Letra obligatoria** + **audio opcional** + **OPS** (letra siempre; audio condicional si hay archivo).
- [x] **Metadata + reloj opcional** — `target_duration_seconds`, título/artista/idioma/mood.
- [x] **Estructura de canción** — Secciones ancladas a índices de línea + reordenación + `structure_warnings`.
- [x] **Inteligencia de letra (LYR)** — Líneas derivadas, ideas heurísticas + LLM opcional, edición y reordenación.
- [x] **Alineación opcional línea ↔ tiempo** — Campo `line_timings_json` (JSON) editable en UI Plan.
- [x] **Intake + dirección + rutas + Creative Lock** — JSON + endpoints lock/unlock + snapshot; bloqueo de mutaciones con lock.
- [x] **Visual Bible + Treatment** — `GET /projects/{id}/documents/preview` + contenido en `export/bundle.md`.
- [x] **Timeline / escenas / shots** — Campos `timeline_plan_json`, `scenes_json`, `shots_json` persistidos + edición JSON en UI (sin editor visual de timeline dedicado).
- [x] **Compilador de prompts** — Genérico / Runway / Kling vía `export/prompts.md?provider=…`.
- [x] **Plan de generación + matriz de revisión** — `generation_plan_json`, `review_matrix_json` persistidos.
- [x] **Exportación v1** — Markdown bundle, **shots.json**, **shots.csv**, prompt packs (v1 no incluye ZIP ni jobs en cola).

### Active (post-MVP / backlog)

- [ ] **Editor visual de timeline** anclado a secciones (sustituir o complementar JSON crudo).
- [ ] **Jobs asíncronos** — Sustituir stub `analysis/enqueue` por pipeline con cola y workers cuando haga falta.
- [ ] **Streaming y curación masiva** en generación LLM de ideas (LYR-02 polish).
- [ ] **Migraciones Alembic** (o equivalente) para evolución de esquema sin borrar DB en prod.

### Out of Scope

- **Render de vídeo por API** desde la app en v1.
- **Análisis musical pesado** (BPM, onsets, curvas de energía, segmentación DSP) en v1 — roadmap *Audio Pro*.
- **EDL / FCPXML / Premiere / Resolve** en v1.
- **Alineación automática perfecta** letra–voz.
- **Colaboración multiusuario en tiempo real** en v1.

## Context

- Nicho: letras muy visuales / narrativa poética; el videoclip debe “honrar” la letra.
- Stack: **Next.js (React, TS, Tailwind)** + **FastAPI (Pydantic, SQLModel/SQLAlchemy)** + SQLite dev / Postgres prod; prompts en `/prompts`. **Workers + librosa** solo cuando activemos *Audio Pro*.
- Repo: **MVP v1 letra-primero** implementado en código (fases 1–6 según ROADMAP); CI en `.github/workflows/ci.yml`.

## Constraints

- **Legal:** derechos explícitos sobre letra; si hay audio u otros assets, mismos estándares.
- **Creativo:** referencias → atributos; no copiar obras o artistas identificables en prompts finales.
- **Técnico:** núcleo agnóstico de proveedor de vídeo.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **Letra primero** como posicionamiento y diseño | Maximiza claridad de valor, reduce coste MVP y riesgo legal vs audio-DSP-first. | ✓ Good (2026-05-13) |
| MVP sin generación de vídeo por API | Valor = dirección + prompts exportables. | ✓ Shipped (MVP) |
| Shot como unidad atómica con herencia de contexto | Evita prompts aislados. | ✓ MVP (`shots_json` + exports) |
| Runway + Kling + genérico como perfiles iniciales | Cobertura práctica de export. | ✓ MVP |
| Documento maestro v1 en `docs/VIDEOZERO-MASTER.md` | Fuente única post-redefinición. | ✓ Good |
| Fase 1 monorepo en repo | Base de ejecución. | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

*Last updated: 2026-05-13 — MVP v1 (letra primero + exports) marcado como validado en código; backlog en Active.*
