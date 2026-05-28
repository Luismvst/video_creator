# Project State

## Project Reference

See: [.planning/PROJECT.md](PROJECT.md)

**Core value:** Herencia de contexto anclada en la **letra** y la **dirección** (lock, biblia, secciones), no en prompts sueltos — con o sin audio.

**Current focus:** Milestone **v2 Render & Direction**. Fases 7–11 (pipeline F1–F5 + E2E) hechas en
dry-run; **Fase 12 (F6 — prompting/dirección de calidad) PLANIFICADA** (7 planes, 5 waves, plan-checker
PASS tras revisión). Siguiente: `/gsd-execute-phase 12`.

## Current Position

Phase: **Roadmap 1 → 6 (MVP code)** marcado completo en [ROADMAP.md](ROADMAP.md)  
Plan: MVP aplicado en repo (sin PLAN.md por subtarea)  
Status: **MVP shipped** — listo para uso interno / demo; backlog en PROJECT → Active  
Last activity: 2026-05-13 — exports `shots.json` / `shots.csv`, recomendaciones en `analysis/enqueue`, CI GitHub Actions.

Progress: [██████████] 100% del **slice MVP** definido en ROADMAP (con backlog explícito para UI avanzada y jobs).

## Performance Metrics

**Velocity:** Phase 1 (3) · 1.5 (3) · 2–6 MVP integrado en iteración única posterior.

## Accumulated Context

### Decisions

- **2026-05-13:** Export v1 incluye Markdown + **JSON + CSV** de shot list (`GET …/export/shots.json`, `…/shots.csv`), coherente con snapshot si hay Creative Lock.
- **2026-05-13:** `POST …/analysis/enqueue` sigue siendo **stub** (no encola jobs) pero devuelve `recommendations[]` accionables.
- **2026-05-13:** CI: workflow `ci.yml` — `pytest` backend + `npm run build` frontend.

### Pending Todos (no bloquean MVP)

- Editor visual de timeline / scene cards (hoy: JSON en pestaña Plan).
- Alembic o migraciones para Postgres.
- Sustituir stub por workers reales cuando el producto lo exija.

### Blockers/Concerns

- SQLite dev: si cambia el modelo, en dev puede seguir haciendo falta borrar `backend/data/videozero.db` hasta tener migraciones.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|---------------|
| Audio | BPM / onsets / curvas / jobs DSP | Deferred | 2026-05-13 |
| Product | Timeline UI dedicada | Backlog | 2026-05-13 |

## Session Continuity

Last session: 2026-05-13  
Stopped at: MVP v1 cerrado en código + documentación alineada; próximo paso natural = milestone review o backlog Active.
