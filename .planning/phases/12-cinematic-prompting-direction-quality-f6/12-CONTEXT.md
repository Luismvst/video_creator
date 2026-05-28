# Phase 12: Cinematic prompting & direction quality (F6) - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning
**Source:** Direct context capture (autor + análisis de código existente)

<domain>
## Phase Boundary

Esta fase **NO añade nuevas etapas al pipeline** (F1–F5 ya existen y funcionan en dry-run).
Eleva la **CALIDAD de la dirección y el prompting** que alimenta al render, para que el videoclip
resultante sea coherente y profesional en lugar de un "collage" genérico.

**Dentro de alcance:**
- Biblia visual estructurada y su inyección en cada prompt (capas).
- Shots ricos por defecto (heurístico mejorado + LLM).
- Modulación de plano/cámara por energía musical (consume F1/F2).
- Keyframe encadenado real (init-image) — el camino real aislado; el plan verificable en dry-run.
- Tuning de prompt por proveedor (Kling/Veo/Runway).
- Reroll dirigido (regenerar solo segmentos marcados).

**Fuera de alcance:**
- Generar vídeo real / gastar en APIs (sigue tras `--run` + `FAL_KEY`).
- Frontend / UI (el usuario quiere el resultado por CLI, no front).
- Nuevas etapas del pipeline o cambios al ensamblado ffmpeg (F5 cerrado).
- Análisis musical nuevo (F1 ya da BPM/beats/energía; aquí solo se **consume**).
</domain>

<decisions>
## Implementation Decisions (LOCKED salvo "Discreción")

### Arquitectura / estilo (heredado del repo — no negociable)
- **stdlib + urllib** para LLM (mismo patrón que `onboarding_ai.py`/`lyrics_insights_engine.py`).
  Sin SDKs pesados nuevos.
- **Degradación elegante sin API key**: todo debe funcionar con heurística local; el LLM solo mejora.
- **Helpers puros testeables** separados del I/O; tests sin red ni binarios.
- **Sin imports pesados a nivel módulo** (CI no instala extras): nada de torch/fal/etc en top-level.
- **No romper la suite** (hoy 48 verdes) ni la forma de segmento que consume F3/F5
  (`index/start_sec/end_sec/duration_sec/shot/prompt_generic/prompt_runway/prompt_kling/source`).

### Biblia visual (DIRQ-01)
- Campos estructurados: `subject` (sujeto/protagonista), `world` (mundo/espacios),
  `palette`, `optics` (óptica/lente, p.ej. 35mm/85mm), `light_rule`, `grain_dof`,
  `style_attributes[]` (derivados de referencias → atributos; **nunca** nombres de obra/artista),
  `negatives[]`.
- Generación: system-prompt LLM dedicado + **fallback heurístico** desde el brief/letra.
- **Persistida** (campo JSON) y **reutilizada en TODOS los segmentos** (no por-shot suelto).
- Vive junto a la dirección existente (`onboarding_ai.py` ya produce `director_answers_json`):
  extender, no duplicar.

### Prompt por capas (DIRQ-02)
- Orden de capas verificable en el texto del prompt:
  `[sujeto+acción de la línea] + [cámara/movimiento] + [biblia: óptica/luz/paleta/grano/DOF] + [negativos] + [aspect/duración]`.
- Sustituye/extiende `prompt_compile.compile_prompt_markdown` (hoy una sola frase fina).
- **La biblia debe aparecer en cada prompt** (test: substring de paleta/óptica presente; bloque
  de negativos presente; aspect presente).

### Shots ricos (DIRQ-03)
- 8–15 planos con intención narrativa por sección (no 2), también **sin key** (heurística mejorada
  que reparte por secciones de letra). LLM eleva calidad cuando hay key.
- Mantener compatibilidad: cada shot conserva `slug/camera/action/notes` + nuevos campos opcionales
  (p.ej. `intent`, `shot_size`).

### Modulación por energía (DIRQ-04)
- Consume la curva de energía/secciones de F1 (`music_analysis`) y los segmentos de F2
  (`music_planner`). Alta energía → planos más cortos ya existe; F6 añade **vocabulario de cámara**
  (push-in/handheld/whip) y **shot size** que escalan con energía.
- Debe degradar: sin audio (solo-letra) usa un perfil neutro.

### Keyframe encadenado real (DIRQ-05)
- `keyframes.py` ya planifica el encadenado. F6 implementa el **camino real**: pasar el último frame
  del clip i-1 (o el keyframe i-1) como **init-image** del image-to-video del segmento i.
- Camino real **aislado** tras `dry_run=False`+`FAL_KEY`; el **plan** (qué referencia a qué) debe ser
  verificable en dry-run sin gastar.

### Tuning por proveedor (DIRQ-06)
- Estructura/vocabulario de prompt óptimos por motor: Kling (sujeto-primero + cámara explícita),
  Veo (descriptivo cinematográfico + audio), Runway (movimiento claro, evitar texto on-screen).
- Encajar en el `provider_prompt`/compilador sin romper los campos `prompt_*` que consume F3.

### Reroll dirigido (DIRQ-07)
- Marcar segmentos (p.ej. `needs_reroll: true` o lista de índices) y regenerar **solo** esos,
  reutilizando el resto. `render_client.render_timeline` ya tiene `limit`; añadir selección por índices.

### Claude's Discretion
- Nombres exactos de funciones/módulos nuevos (p.ej. `visual_bible.py` vs extender `onboarding_ai.py`).
- Formato interno exacto del prompt por capas (mientras cumpla el orden y los tests).
- Vocabulario concreto de cámara por nivel de energía.
- Si la biblia se genera en su propia llamada LLM o se funde con la de shots.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Diseño v2 y estado
- `.planning/V2-RENDER-PIPELINE.md` — diseño completo del pipeline v2, motores, costes, §7 revisión de prompting.
- `.planning/ROADMAP.md` — Phase 12 (criterios de éxito) + fases 7–11 (qué existe).
- `.planning/REQUIREMENTS.md` — DIRQ-01..07.
- `CLAUDE.md` — reglas del proyecto (alcance por fase, legal).

### Código a extender (source of truth de patrones)
- `backend/app/prompt_compile.py` — compilador actual (plantilla fina a sustituir por capas).
- `backend/app/onboarding_ai.py` — dirección/shots/biblia (heurístico + LLM vía urllib).
- `backend/app/lyrics_insights_engine.py` — patrón de config OpenAI (`_openai_api_key/_openai_model/openai_configured`).
- `backend/app/music_planner.py` — segmentos (dónde inyectar energía→cámara); `plan_timeline`, `_materialize`.
- `backend/app/music_analysis.py` — curva de energía/secciones disponibles.
- `backend/app/render_client.py` — `provider_prompt`, `render_segment/render_timeline` (tuning + reroll).
- `backend/app/keyframes.py` — encadenado (init-image real).
- `backend/tests/` — estilo de tests puros (p.ej. `test_render_client.py`, `test_music_planner.py`).
</canonical_refs>

<specifics>
## Specific Ideas

- Ejemplo de prompt por capas objetivo (Kling), sujeto-primero:
  "Mujer de espaldas en un puerto nevado al amanecer, camina hacia el faro; cámara: push-in lento
  85mm, poca profundidad de campo; luz: contraluz frío azulado, niebla, grano sutil 16mm; negativos:
  texto en pantalla, deformidad de manos, marca de agua; 16:9, 4s."
- Comparativa antes/después: el usuario quiere poder ver el `segments.json` (prompts) de antes vs F6
  sin gastar (mini-demo lado a lado sería un buen artefacto de verificación).
- Recordatorio realista (documentar, no resolver en F6): "excepcional" exige además curación/reroll
  humano; F6 sube el suelo de calidad y deja el reroll dirigido como herramienta.
</specifics>

<deferred>
## Deferred Ideas

- Curación humana asistida / UI de revisión de tomas (no en F6; el usuario no quiere front).
- Aprendizaje de prompts a partir de tomas aceptadas/rechazadas.
- Soporte de más proveedores allá de Kling/Veo/Runway/Wan.
</deferred>

---

*Phase: 12-cinematic-prompting-direction-quality-f6*
*Context gathered: 2026-05-29 (direct capture)*
