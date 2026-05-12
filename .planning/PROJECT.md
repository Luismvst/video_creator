# VideoZero

## What This Is

**VideoZero** es una aplicación que guía a músicos y creadores no técnicos desde **canción + letra (+ referencias opcionales)** hasta un **paquete de producción coherente** para videoclips con IA: interpretación, dirección creativa, biblia visual, treatment, timeline por secciones, escenas, shot list, prompts por proveedor (compilación, no render unificado), plan de generación, checklist y matriz de revisión. La unidad central del sistema es el **Shot** anclado a la jerarquía Song → Section → Scene → Shot, no un prompt suelto.

**Fuente de verdad de producto:** [docs/VIDEOZERO-MASTER.md](../docs/VIDEOZERO-MASTER.md) (v0.2).

## Core Value

Que cada plano y cada export **herede** contexto validado (letra, tiempo, sección musical, emoción, biblia visual, reglas de continuidad y proveedor objetivo), de modo que el usuario pueda producir en herramientas externas (Runway, Veo/Flow, Kling, Luma, etc.) **sin collage incoherente**.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Workspace por canción con persistencia y revisión de estado del flujo guiado.
- [ ] Ingesta: audio, letra (pegar/subir), metadata básica (título, artista, idioma, mood).
- [ ] Análisis de audio heurístico (duración, BPM aprox, onsets, energía, segmentación tentativa, curva de intensidad).
- [ ] Análisis de letra estructurado (líneas/bloques, anclas visuales, propuestas interpretativas).
- [ ] Alineación letra ↔ tiempo en tabla editable (start/end, sección, intensidad, notas).
- [ ] Flujo de investigación creativa y motor de decisiones de director (preguntas concretas, respuestas persistidas).
- [ ] Rutas creativas múltiples, elección/mezcla y **Creative Lock** versionado antes de planificación densa.
- [ ] Generación de **Visual Bible** y **Treatment** exportables.
- [ ] Timeline por secciones, scene cards y shot list editables.
- [ ] Compilador de prompts canónico + al menos dos perfiles de proveedor además del genérico (por defecto: **Runway** + **Kling** hasta decisión explícita).
- [ ] Plan de generación, checklist y matriz de revisión por plano.
- [ ] Exportación v1: Markdown (brief, preguntas, bible, treatment, timeline, edit plan), CSV + JSON shot list, prompt packs `.md` por proveedor.
- [ ] Confirmación de derechos de uso del audio antes de procesamiento pesado (checkbox + copy legal mínimo).

### Out of Scope

- **Render de vídeo por API** desde la app en v1 — el valor es el paquete de dirección y prompts.
- **EDL / FCPXML / Premiere / Resolve** — fases posteriores.
- **Alineación automática perfecta** letra–voz; solo asistida + edición manual confiable.
- **Colaboración multiusuario en tiempo real** — post-MVP.

## Context

- Nicho inicial: cantautor, letras muy visuales y narrativas poéticas.
- Stack acordado (MVP): **Next.js (React, TS, Tailwind, shadcn/ui)** + **FastAPI (Pydantic, SQLModel/SQLAlchemy)** + SQLite dev / Postgres prod + workers para análisis de audio + SSE/WebSocket para progreso; **ffmpeg + librosa**; prompts LLM versionados fuera del código (`/prompts`).
- Decisiones pendientes de producto: ver §13 en [docs/VIDEOZERO-MASTER.md](../docs/VIDEOZERO-MASTER.md).

## Constraints

- **Legal / creativo**: referencias traducidas a atributos; no copiar obras o artistas identificables en prompts finales; consentimiento explícito para fotos de personas reales.
- **Técnico**: núcleo **agnostic** respecto a proveedor de vídeo; adaptadores por perfil.
- **Calidad**: reglas anti-collage (anclas por escena, límite configurable de planos por bloque, continuidad explícita).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| MVP sin generación de vídeo por API | Reduce riesgo y acelera valor (treatment + shot list + prompt packs). | — Pending |
| Shot como unidad atómica con herencia de contexto | Evita prompts aislados y collage. | — Pending |
| Perfiles de proveedor por defecto Runway + Kling (además de genérico) | Cumple “≥2 proveedores” del master hasta que el usuario elija otros. | — Pending |
| Documento maestro en repo `docs/VIDEOZERO-MASTER.md` | Una fuente para GSD y para el equipo. | ✓ Good |

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

*Last updated: 2026-05-13 after GSD project initialization from VIDEOZERO-MASTER.md*
