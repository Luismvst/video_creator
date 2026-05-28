# Phase 12: Cinematic prompting & direction quality (F6) — Research

**Researched:** 2026-05-29
**Domain:** Prompting cinematográfico para motores de vídeo-IA (Kling 3.0 / Veo 3.1 / Runway Gen-4.x), continuidad anti-collage, modulación por energía musical, dirección de prompts por capas — todo en dry-run, lógica de texto pura.
**Confidence:** MEDIUM-HIGH (estructura de prompt y vocabulario por motor: HIGH, verificados con docs oficiales/guías 2026; arquitectura de código: HIGH, leída del repo; heurísticas de mapeo energía→cámara: MEDIUM, convención + diseño propio)

## Summary

F6 no construye pipeline nuevo: el flujo F1→F5 (`audio_ingest` → `music_planner` → `render_client` → `keyframes` → `video_assembly`, orquestado por `pipeline.run_pipeline`) ya existe y pasa 48 tests en dry-run. F6 eleva la **calidad del texto que entra al motor** y el **plan de continuidad**, sin gastar APIs. Todo lo que F6 añade es **texto determinista + estructura de datos**, lo cual es 100% testeable con asserts puros — encaja perfecto con el estilo del repo (stdlib, helpers puros, degradación sin key).

El hallazgo central de la investigación: los tres motores objetivo convergen en 2026 hacia una **estructura de prompt por capas con orden explícito**, pero difieren en matices que importan para el tuning (DIRQ-06):
- **Kling 3.0**: sujeto-primero, cámara explícita con vocabulario de Hollywood **al final** de la frase, 5-7 elementos máximo, soporta **negativos** como campo/sufijo, exige *motion endpoints* ("...then settles") para evitar cuelgues.
- **Veo 3.1**: fórmula `[Cinematografía] + [Sujeto] + [Acción] + [Contexto] + [Estilo/Ambiente]` (cámara **primero**), descriptivo tipo "tratamiento de director", soporta dirección de audio y negativos por *exclusión descriptiva* (no la palabra "no").
- **Runway Gen-4.x**: image-to-video céntrico — el prompt describe **movimiento, no apariencia** (la apariencia la fija la init-image); **NO soporta frases negativas** (las ignora o invierte); mantener simple, una moción primaria + una secundaria.

La continuidad anti-collage real (DIRQ-05) hoy se logra con **last-frame chaining** (último frame del clip i-1 → init-image del clip i) + **biblia visual fija inyectada en todos los prompts** (DIRQ-01/02) + clips cortos (3-10s, ya garantizado por `max_clip`). `keyframes.py` ya planifica el encadenado; F6 cierra el camino real (aislado tras `dry_run=False`+`FAL_KEY`) y hace que el **plan de referencias** sea verificable en dry-run.

**Primary recommendation:** Crear un módulo de **biblia visual estructurada** (`visual_bible.py`, helper puro + fallback heurístico + LLM opcional vía el patrón `onboarding_ai`) y un **compilador de prompt por capas por proveedor** que sustituya la plantilla fina de `prompt_compile.compile_prompt_markdown`. Inyectar la biblia en cada segmento dentro de `music_planner._materialize`. Añadir un **mapa energía→vocabulario de cámara** puro consumido en `_materialize`/`_split_max`. Cerrar last-frame chaining en `keyframes.py` (campo `last_frame_ref` en el plan) y `render_client` (pasar `image_url`). Añadir selección por índices (`reroll_indices`) a `render_timeline`. Verificar TODO con asserts de substring sobre el texto del prompt — sin red ni binarios.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Biblia visual estructurada (DIRQ-01) | Generación de dirección (`onboarding_ai`/nuevo `visual_bible`) | LLM opcional (urllib) | Es contenido de texto derivado de brief/letra; debe persistir y reutilizarse |
| Prompt por capas (DIRQ-02) | Compilador (`prompt_compile`) | Planner (`music_planner._materialize` lo invoca por segmento) | El texto del prompt es responsabilidad del compilador; el planner solo lo orquesta |
| Shots ricos (DIRQ-03) | Generación de dirección (heurística + LLM) | — | Misma capa que produce `shots_json` hoy |
| Modulación energía→cámara (DIRQ-04) | Planner (`music_planner`) | Análisis musical (`music_analysis`, ya da secciones/energía) | El planner ya consume energía para troceo; F6 añade vocabulario de cámara aquí |
| Keyframe encadenado real (DIRQ-05) | Keyframes (`keyframes.py`) + Render (`render_client`) | — | El plan vive en keyframes; el paso init-image lo ejecuta render_client |
| Tuning por proveedor (DIRQ-06) | Compilador (`prompt_compile` por-proveedor) | Render (`provider_prompt` selecciona el campo) | Estructura de texto por motor = compilador; selección de campo ya existe |
| Reroll dirigido (DIRQ-07) | Render (`render_client.render_timeline`) | — | Es selección de subconjunto de segmentos a regenerar |

## Standard Stack

**No se añade ninguna librería nueva.** El stack está congelado por CLAUDE.md / CONTEXT.md: stdlib + urllib, sin SDKs pesados, sin imports pesados a nivel módulo. El "stack" de F6 son patrones de texto y estructura de datos.

### Core (ya en el repo, se extiende)
| Módulo | Rol en F6 | Por qué es el punto correcto |
|--------|-----------|------------------------------|
| `backend/app/prompt_compile.py` | Sustituir `compile_prompt_markdown` por compilador por capas por proveedor | `[CITED: CONTEXT.md DIRQ-02]` Es el "plantilla fina a sustituir" |
| `backend/app/onboarding_ai.py` | Generar biblia visual (extender o módulo nuevo `visual_bible.py`) | `[VERIFIED: lectura de repo]` Ya produce `director_answers_json`, patrón LLM-urllib + fallback heurístico |
| `backend/app/lyrics_insights_engine.py` | Reusar `_openai_api_key/_openai_model/openai_configured` | `[VERIFIED: repo líneas 121-131]` Config OpenAI centralizada |
| `backend/app/music_planner.py` | Inyectar biblia + cámara-por-energía en `_materialize`; modular `_split_max` | `[VERIFIED: repo]` Único punto donde se construyen los `prompt_*` por segmento |
| `backend/app/music_analysis.py` | Consumir `sections`/`mean_energy` (ya existe) | `[VERIFIED: repo]` `_section_energy_threshold`/`_is_high_energy` ya implementados |
| `backend/app/keyframes.py` | Cerrar last-frame chaining real; plan `reference_image` ya existe | `[VERIFIED: repo líneas 64-81]` `reference_image=prev_path` ya planificado |
| `backend/app/render_client.py` | `image_url` para i2v + `reroll_indices` en `render_timeline` | `[VERIFIED: repo]` `provider_prompt`/`limit` ya existen |

### Decisión de diseño (Claude's Discretion en CONTEXT.md)
| Decisión | Recomendación | Razón |
|----------|---------------|-------|
| ¿Módulo nuevo o extender? | **Módulo nuevo `visual_bible.py`** con helpers puros, importado por `onboarding_ai` | Mantiene `onboarding_ai` legible; helper puro `build_visual_bible(brief, lyrics, ...) -> dict` testeable sin red |
| ¿Biblia en llamada LLM propia o fundida con shots? | **Fundida** en `llm_onboarding_package` (añadir clave `"visual_bible"` al JSON pedido) + fallback heurístico propio | 1 llamada en vez de 2 (coste/latencia); el fallback heurístico vive en `visual_bible.py` |
| Formato del prompt por capas | String con separadores `; ` entre capas, orden fijo verificable | Asserts de substring simples; legible para el usuario en `segments.json` |

**Installation:** Ninguna. CI no instala extras. No tocar `requirements-audio.txt`.

## Architecture Patterns

### System Architecture Diagram (flujo de datos F6 dentro del pipeline existente)

```
brief + letra ──────────────────────────────┐
                                             ▼
                          [visual_bible.build_visual_bible]   ← DIRQ-01
                          (heurístico ∥ LLM 1 llamada)
                          → bible{subject, world, palette, optics,
                                  light_rule, grain_dof,
                                  style_attributes[], negatives[]}
                                             │ (persistida en Song, JSON)
                                             │
letra + (audio→F1) ──► [onboarding shots ricos 8-15]  ← DIRQ-03
                                             │
                                             ▼
music{beats,sections,energy} ──► [music_planner.plan_timeline]
   │                                         │
   │  energy/section ──► [energy→camera map] ─┤  ← DIRQ-04
   │  (shot_size + movimiento escalan con energía)
   ▼                                         ▼
                          [_materialize: por cada segmento]
                                             │
                          [prompt_compile.compile_layered_prompt(  ← DIRQ-02 + DIRQ-06
                              line_subject, camera_layer, bible, provider)]
                          → prompt_generic / prompt_kling /
                            prompt_runway / prompt_veo   (capas en orden)
                                             │
                                             ▼
                    segments[] {..., shot{shot_size,intent}, prompt_*}
                                             │
              ┌──────────────────────────────┤
              ▼                               ▼
[keyframes.plan_keyframes chain=True]   [render_client.render_timeline]
 last_frame_ref: kf_{i-1} → init i  ← DIRQ-05   reroll_indices=[...]  ← DIRQ-07
 (plan en dry-run; i2v real tras FAL_KEY)        image_url=last_frame (i2v)
              └──────────────┬───────────────┘
                             ▼
                  [video_assembly] (F5, sin cambios)
                             ▼
                    videoclip_final.mp4
```

### Recommended additions (no nueva carpeta)
```
backend/app/
├── visual_bible.py        # NUEVO: build_visual_bible (heurístico) + esquema; helpers puros
├── prompt_compile.py      # EXTENDER: compile_layered_prompt(provider) + bloques por capa
├── camera_language.py     # NUEVO (opc.): mapa energía→{shot_size, camera_move}; puro
├── onboarding_ai.py       # EXTENDER: shots ricos 8-15 + fusionar biblia en LLM/heurístico
├── music_planner.py       # EXTENDER: inyectar biblia+cámara en _materialize
├── keyframes.py           # EXTENDER: last_frame_ref real (campo en plan)
└── render_client.py        # EXTENDER: image_url (i2v) + reroll_indices
```

### Pattern 1: Prompt por capas con orden verificable (DIRQ-02)
**What:** Cada prompt de segmento se ensambla concatenando capas en orden fijo, de modo que un test pueda afirmar la presencia y el orden de cada bloque por substring.
**When to use:** En `compile_layered_prompt`, invocado desde `_materialize` por segmento y proveedor.
**Orden objetivo** `[CITED: CONTEXT.md líneas 52-53]`:
`[sujeto+acción de la línea] + [cámara/movimiento] + [biblia: óptica/luz/paleta/grano/DOF] + [negativos] + [aspect/duración]`

```python
# Patrón (puro, sin I/O). Orden y separadores fijos → testeable por substring/índice.
def compile_layered_prompt(*, subject_action, camera, bible, provider, aspect, duration_sec):
    palette = bible.get("palette", "")
    optics  = bible.get("optics", "")
    light   = bible.get("light_rule", "")
    grain   = bible.get("grain_dof", "")
    negs    = ", ".join(bible.get("negatives", []))
    bible_layer = f"luz {light}; {optics}; paleta {palette}; {grain}"
    clock = f"{aspect}, {int(round(duration_sec))}s"

    if provider == "kling":
        # sujeto-primero, cámara explícita AL FINAL, negativos como sufijo
        return f"{subject_action}; {bible_layer}; cámara: {camera}; negativos: {negs}; {clock}"
    if provider == "veo":
        # cinematografía PRIMERO (fórmula Veo), negativos por exclusión descriptiva
        return f"{camera}, {subject_action}, {bible_layer}, {clock}. Evitar: {negs}"
    if provider == "runway":
        # describe MOVIMIENTO, no apariencia; SIN frases negativas (Runway las ignora/invierte)
        return f"{subject_action}; movimiento de cámara: {camera}; {bible_layer}; {clock}"
    # generic
    return f"{subject_action}; cámara: {camera}; {bible_layer}; negativos: {negs}; {clock}"
```

### Pattern 2: Biblia visual estructurada + fallback heurístico (DIRQ-01)
**What:** Dict con campos fijos, generado por LLM cuando hay key, por heurística desde brief/letra cuando no. Se persiste y se reutiliza en TODOS los segmentos (no por-shot suelto).
**Campos** `[CITED: CONTEXT.md líneas 42-45]`: `subject`, `world`, `palette`, `optics` (p.ej. 35mm/85mm), `light_rule`, `grain_dof`, `style_attributes[]` (derivados de referencias → atributos), `negatives[]`.
```python
# Fallback heurístico (mismo espíritu que _keyword_attrs en onboarding_ai)
def build_visual_bible(brief, lyrics_text, *, mood=None) -> dict:
    attrs = _keyword_attrs(brief or lyrics_text)   # reusar pool existente
    return {
        "subject": "protagonista anclado a la primera imagen de la letra",
        "world": _infer_world(brief, lyrics_text),
        "palette": _infer_palette(mood, brief),     # p.ej. "fría azulada, neón"
        "optics": "85mm, poca profundidad de campo",
        "light_rule": "contraluz frío, niebla suave",
        "grain_dof": "grano sutil 16mm, DOF cerrado",
        "style_attributes": attrs,                   # nunca nombres de obra/artista
        "negatives": DEFAULT_NEGATIVES,
    }
```

### Pattern 3: Mapeo energía → vocabulario de cámara (DIRQ-04)
**What:** Función pura que, dada la energía relativa de la sección (alta/media/baja), devuelve `shot_size` y `camera_move`. Degrada a perfil neutro sin audio.
`[CITED: soundonsound.com, filtergrade.com — convención de videoclip]` Estribillo/alta energía → cortes rápidos (ya implementado vía `high_energy_factor`), planos más cerrados/dinámicos, push-in/handheld/whip; verso/baja energía → planos sostenidos, dolly lento, wide.
```python
# Niveles derivados de mean_energy vs mediana (reusar _section_energy_threshold)
ENERGY_CAMERA = {
    "high":   {"shot_size": "primer plano / plano medio corto",
               "camera_move": "push-in rápido, handheld, whip-pan"},
    "mid":    {"shot_size": "plano medio",
               "camera_move": "dolly suave, tracking lateral"},
    "low":    {"shot_size": "plano general sostenido",
               "camera_move": "cámara estática o pan muy lento"},
    "neutral":{"shot_size": "plano medio",          # sin audio (solo-letra)
               "camera_move": "movimiento contenido"},
}
def camera_for_energy(level: str) -> dict:
    return ENERGY_CAMERA.get(level, ENERGY_CAMERA["neutral"])
```

### Pattern 4: Last-frame chaining real (DIRQ-05)
**What:** El plan de keyframes ya marca `reference_image=prev_path`. F6 hace que (a) el plan exponga explícitamente la referencia init-image por segmento (verificable en dry-run) y (b) el camino real pase esa imagen como `image_url` al modelo image-to-video de fal.
`[VERIFIED: WebSearch magichour.ai/renderfire 2026]` Usar el último frame de la escena anterior como primer frame de la siguiente fuerza continuidad porque el modelo arranca donde acabó el clip previo. Límite real: clips 3-10s; identidad de personaje se degrada en clips largos (por eso `max_clip` ya ayuda).
- En dry-run, `plan_keyframes` (chain=True) ya produce `reference_image` encadenado → test verifica que el seg i referencia al kf del seg i-1 y el primero `None`.
- Camino real: `render_segment(..., image_url=<último frame/keyframe>)` → payload fal incluye `image_url` para el modelo i2v (campo configurable por entorno, como el resto).

### Pattern 5: Reroll dirigido (DIRQ-07)
**What:** `render_timeline(..., reroll_indices=[3,7,12])` renderiza solo esos segmentos (por `index`), reutilizando el resto. Complementa el `limit` ya existente.
```python
# selección por índices (1-based, como el campo `index`)
if reroll_indices:
    to_render = [s for s in segments if s.get("index") in set(reroll_indices)]
```

### Anti-Patterns to Avoid
- **Frases negativas en Runway:** `[CITED: help.runwayml.com Gen-4 guide]` Gen-4 NO soporta negativos; "no text on screen" puede producir el efecto contrario. Para Runway, expresar lo deseado en positivo y omitir el bloque de negativos.
- **Mezclar términos de iluminación contradictorios:** `[CITED: veed.io/ambienceai Kling guide]` mezclar "golden hour" + "studio lighting" confunde al modelo. La biblia debe fijar UNA regla de luz coherente.
- **Sobrecargar el prompt (Kling):** `[CITED: fal.ai Kling 2.6 guide]` 2.5 Turbo 3-4 elementos, 2.6 soporta 5-7. No meter 15 atributos; la biblia debe ser concisa.
- **Camera move sin endpoint (Kling):** `[CITED: ambienceai]` movimiento abierto causa "99% hangs"; añadir punto final de movimiento.
- **Describir apariencia en Runway i2v:** `[CITED: help.runwayml.com]` la apariencia la fija la init-image; el prompt debe describir el movimiento.
- **Biblia por-shot suelta:** `[CITED: CONTEXT.md línea 47]` la biblia es única y se reutiliza; generar una distinta por shot rompe la continuidad.

## Don't Hand-Roll

| Problema | No construir | Usar en su lugar | Por qué |
|----------|--------------|------------------|---------|
| Análisis de energía/secciones | DSP propio | `music_analysis.sections_from_energy` / `_section_energy_threshold` (ya existen) | F1 ya lo da; DIRQ-04 solo **consume** |
| Troceo más rápido en estribillo | Lógica nueva de cortes | `_split_max(high_energy_factor=...)` (ya existe) | DIRQ-04 añade vocabulario de cámara, no re-trocea |
| Config/llamada OpenAI | Nuevo cliente HTTP | `_openai_api_key/_openai_model/openai_configured` + patrón `urllib` de `onboarding_ai`/`lyrics_insights_engine` | Patrón estable, degradación sin key probada |
| Plan de encadenado de keyframes | Estructura nueva | `keyframes.plan_keyframes(chain=True)` (ya encadena `reference_image`) | F6 solo expone/usa la referencia |
| Estimación de coste / gate presupuesto | Recalcular | `estimate_render_cost` / `within_budget` (ya existen) | Reroll dirigido reusa la estimación sobre el subconjunto |
| Selección de prompt por proveedor | Nuevo switch | `render_client.provider_prompt` (ya hace fallback a genérico) | Solo añadir campo `prompt_veo` si se quiere; el resto encaja |

**Key insight:** F6 es casi enteramente **composición de texto + datos sobre piezas ya construidas**. El riesgo no es técnico (no hay red ni binarios), es de **regresión**: romper la forma del segmento que consumen F3/F5 o la suite de 48 tests. Cualquier campo nuevo en `shot`/`segment` debe ser **aditivo y opcional**.

## Runtime State Inventory

> No aplica como rename/refactor. Pero F6 toca la **forma de datos persistida**, así que documento el estado que debe permanecer compatible:

| Categoría | Items | Acción requerida |
|-----------|-------|------------------|
| Forma de segmento (consumida por F3/F5) | `index/start_sec/end_sec/duration_sec/shot/prompt_generic/prompt_runway/prompt_kling/source` `[CITED: CONTEXT.md línea 39]` | NO romper: campos nuevos (`prompt_veo`, `shot.shot_size`, `shot.intent`) deben ser **aditivos** |
| Campo persistido de dirección | `Song.director_answers_json` / `shots_json` / `creative_intake_json` `[VERIFIED: onboarding_ai + test_smoke]` | Añadir `visual_bible_json` (nuevo campo JSON) o anidarlo; persistir y reutilizar |
| Tarifas/modelos fal por proveedor | `PROVIDERS[*].fal_model` configurables por env `[VERIFIED: render_client líneas 43-69]` | Si i2v necesita modelo distinto a t2v, añadir `fal_model_i2v` configurable (no hardcodear) |
| Suite de tests | 48 verdes `[CITED: V2-RENDER-PIPELINE.md línea 335]` | No romper; añadir tests nuevos por DIRQ |

## Common Pitfalls

### Pitfall 1: Romper la forma del segmento → cae F3/F5 y la suite
**What goes wrong:** Renombrar o reordenar claves de `segment`/`shot`; `render_client.provider_prompt` o `video_assembly` dejan de encontrar `prompt_*`.
**Why:** F3/F5 leen claves por nombre exacto.
**How to avoid:** Solo añadir claves opcionales. Tests existentes (`test_render_client`, `test_music_planner`) deben seguir verdes sin tocarlos.
**Warning signs:** Cualquier `KeyError` o test rojo en `test_render_client.py`.

### Pitfall 2: Negativos aplicados a Runway
**What goes wrong:** Inyectar bloque "negativos:" en el prompt de Runway empeora el resultado.
**Why:** `[CITED: help.runwayml.com]` Gen-4 no soporta frases negativas.
**How to avoid:** El compilador por proveedor **omite** la capa de negativos para `runway`; el test debe afirmar que el prompt runway NO contiene "negativos:".

### Pitfall 3: Biblia ausente en algún prompt
**What goes wrong:** Algún segmento sin shot (`m==0` en `_materialize`) produce `prompt_* = ""`.
**Why:** `[VERIFIED: music_planner línea 132]` hoy si no hay shot, el prompt va vacío.
**How to avoid:** Con DIRQ-03 (8-15 shots por defecto) siempre habrá shots; aun así, el compilador debe inyectar la biblia aunque el shot sea pobre. Test: la paleta y la óptica aparecen en **todos** los `prompt_generic` no vacíos.

### Pitfall 4: LLM devuelve nombres de obra/artista (riesgo legal)
**What goes wrong:** El modelo cuela "estilo de [artista]" en `style_attributes` o en la biblia.
**Why:** Prompts de referencia mal formulados.
**How to avoid:** `[CITED: CONTEXT.md + REQUIREMENTS CRE-01]` system-prompt explícito "referencias→atributos, nunca nombres de obras/artistas"; **y** un filtro heurístico post-LLM (lista de palabras "estilo de", "como [Nombre]") que limpie. Test puro: dada una biblia con un nombre prohibido en `style_attributes`, el sanitizador lo elimina.

### Pitfall 5: Modulación de cámara sin audio rompe
**What goes wrong:** `sections` es `None` (solo-letra) y el código asume secciones.
**Why:** Branch solo-letra no tiene energía.
**How to avoid:** `[VERIFIED: music_planner._is_high_energy ya devuelve False sin secciones]` `camera_for_energy` cae a `"neutral"`. Test: sin `music`, todos los segmentos llevan perfil neutro.

## Code Examples

### Verificación por substring del orden de capas (test puro objetivo)
```python
# tests/test_prompt_compile.py (estilo de test_render_client: puro, sin red)
def test_layered_prompt_kling_order_and_bible_present():
    bible = {"palette": "fría neón", "optics": "85mm", "light_rule": "contraluz frío",
             "grain_dof": "grano 16mm", "negatives": ["texto en pantalla", "manos deformes"]}
    p = compile_layered_prompt(subject_action="mujer camina hacia el faro",
                               camera="push-in lento", bible=bible, provider="kling",
                               aspect="16:9", duration_sec=4)
    assert "mujer camina" in p                       # sujeto primero
    assert "fría neón" in p and "85mm" in p          # biblia presente
    assert "negativos:" in p and "texto en pantalla" in p
    assert "16:9" in p and "4s" in p                 # aspect/duración
    assert p.index("mujer") < p.index("cámara:")     # sujeto antes que cámara (Kling)

def test_layered_prompt_runway_has_no_negatives():
    p = compile_layered_prompt(subject_action="x", camera="dolly", bible={"negatives":["y"]},
                               provider="runway", aspect="16:9", duration_sec=4)
    assert "negativos:" not in p                     # Runway no soporta negativos
```

### Last-frame chaining verificable en dry-run
```python
def test_keyframe_chain_references_previous():
    segs = [{"index": i, "shot": {"action": f"a{i}"}} for i in (1, 2, 3)]
    plan = plan_keyframes(segs, chain=True, dry_run=True)
    kfs = plan["keyframes"]
    assert kfs[0]["reference_image"] is None         # el primero no encadena
    assert kfs[1]["reference_image"].endswith("kf_001.png")  # i refiere a i-1
    assert kfs[2]["reference_image"].endswith("kf_002.png")
```

### Reroll dirigido
```python
def test_reroll_only_marked_indices():
    res = render_timeline(_segs(10), provider="kling", dry_run=True, reroll_indices=[2, 5])
    rendered = [r["index"] for r in res["segments"]]
    assert rendered == [2, 5]
```

## State of the Art

| Old Approach | Current Approach (2026) | Impact en F6 |
|--------------|-------------------------|--------------|
| Una sola frase por shot (`compile_prompt_markdown`) | Prompt por capas con orden por proveedor | Sustituir compilador (DIRQ-02/06) |
| Negativos universales | Negativos sí en Kling/Veo, **no** en Runway | Branch por proveedor en negativos |
| t2v independiente por clip | i2v con last-frame chaining + character/reference locking | Cerrar DIRQ-05; Veo "Ingredients", Kling "character lock" |
| Camera move implícito | Camera move **explícito** + motion endpoint (Kling); cinematografía-primero (Veo) | Vocabulario explícito por energía (DIRQ-04) |
| Sora 2 como opción | **Sora 2 deprecado** (API off 24-sep-2026) `[CITED: V2-RENDER-PIPELINE §10]` | No incluir Sora |

**Deprecado/evitar:** Sora 2 (API se apaga sep-2026). Spotify para audio (cifrado). Frases "no X" en Runway.

## Validation Architecture

> `nyquist_validation: true` en config.json → sección incluida. Todo se valida con **tests puros: sin red, sin binarios, sin FAL_KEY**, igual que `test_render_client.py`/`test_music_planner.py`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `[VERIFIED: backend/tests/*.py]` |
| Config file | ninguno dedicado; tests bajo `backend/tests/`, import `from app.X import ...` |
| Quick run command | `cd backend && python -m pytest tests/test_prompt_compile.py -x -q` |
| Full suite command | `cd backend && python -m pytest -q` (debe seguir ≥48 verdes + nuevos) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| DIRQ-01 | Biblia tiene todos los campos; heurística sin key; LLM no cuela nombres de obra (sanitizador) | unit | `pytest tests/test_visual_bible.py -x` | ❌ Wave 0 |
| DIRQ-02 | Prompt incluye, en orden, sujeto+cámara+biblia+negativos+aspect; biblia presente en TODOS los segmentos | unit | `pytest tests/test_prompt_compile.py -x` | ❌ Wave 0 |
| DIRQ-03 | Ruta heurística genera 8-15 shots con `intent`/`shot_size`, sin key | unit | `pytest tests/test_onboarding_ai.py -k shots_richness -x` | ❌ Wave 0 (no hay test de onboarding hoy) |
| DIRQ-04 | `camera_for_energy` mapea high/mid/low/neutral; sin audio → neutral; alta energía → plano más corto/dinámico | unit | `pytest tests/test_camera_language.py -x` | ❌ Wave 0 |
| DIRQ-05 | Plan de keyframes encadena (`reference_image` = kf anterior; primero None); render real pasa `image_url` (mock dry-run) | unit | `pytest tests/test_keyframes.py -k chain -x` | ⚠️ archivo no existe; keyframes.py sin test hoy |
| DIRQ-06 | Kling sujeto-primero+negativos sufijo; Veo cámara-primero; Runway sin negativos + describe movimiento | unit | `pytest tests/test_prompt_compile.py -k provider -x` | ❌ Wave 0 |
| DIRQ-07 | `render_timeline(reroll_indices=[...])` renderiza solo esos índices; estimación sobre el subconjunto | unit | `pytest tests/test_render_client.py -k reroll -x` | ⚠️ extender existente |

### Sampling Rate
- **Per task commit:** `pytest tests/test_<módulo_tocado>.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest -q` (suite completa)
- **Phase gate:** suite completa verde (≥48 + nuevos) antes de `/gsd-verify-work`

### Artefacto de verificación recomendado (CONTEXT.md "Specifics")
`[CITED: CONTEXT.md líneas 121-123]` Mini-demo antes/después sin gastar: un test/CLI que tome un `shots_json` + brief y emita `segments.json` con prompts F6 vs prompt fino anterior, para comparar lado a lado. Verificable: el prompt F6 contiene biblia+negativos+aspect que el anterior no.

### Wave 0 Gaps
- [ ] `tests/test_visual_bible.py` — DIRQ-01 (campos, heurística, sanitizador legal)
- [ ] `tests/test_prompt_compile.py` — DIRQ-02/06 (orden de capas, branch por proveedor)
- [ ] `tests/test_camera_language.py` — DIRQ-04 (mapa energía→cámara, neutral sin audio)
- [ ] `tests/test_keyframes.py` — DIRQ-05 (encadenado; hoy `keyframes.py` no tiene test)
- [ ] `tests/test_onboarding_ai.py` — DIRQ-03 (riqueza de shots; hoy onboarding no tiene test unit dedicado, solo vía smoke API)
- [ ] Extender `tests/test_render_client.py` — DIRQ-07 (`reroll_indices`) y DIRQ-05 (`image_url` en payload dry-run)
- [ ] Extender `tests/test_music_planner.py` — biblia inyectada en cada `prompt_*`; cámara-por-energía en `shot`

## Security Domain

> `security_enforcement` no está en config.json → tratar como habilitado por defecto, pero el ámbito de F6 es texto/datos en local sin red en CI. ASVS de superficie web no aplica al código nuevo de F6.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V5 Input Validation | sí (parsing JSON del LLM) | `json.loads` con try/except + validación de forma (patrón ya usado en `onboarding_ai` líneas 218-244) |
| V6 Cryptography | no | — |
| Secret handling | sí | API keys solo por env (`_openai_api_key`, `FAL_KEY`); nunca en prompts, logs ni `segments.json` |
| Compliance / IP (legal) | **sí (crítico)** | `[CITED: CRE-01 + CONTEXT.md]` referencias→atributos; **sanitizador** que elimina nombres de obra/artista de la biblia y prompts; test que lo verifica |

### Known Threat Patterns
| Pattern | STRIDE | Mitigación |
|---------|--------|------------|
| LLM inyecta nombre de obra/artista en biblia/prompt | Information disclosure / IP infringement | system-prompt restrictivo + sanitizador heurístico post-LLM + test |
| JSON malformado del LLM rompe el flujo | DoS | try/except + fallback heurístico (patrón existente) |
| Secret en `segments.json` exportable | Info disclosure | nunca incluir keys; prompts no contienen secretos |

## Sources

### Primary (HIGH confidence)
- Lectura directa del repo: `prompt_compile.py`, `render_client.py`, `keyframes.py`, `onboarding_ai.py`, `music_planner.py`, `music_analysis.py`, `lyrics_insights_engine.py`, `tests/test_render_client.py`, `tests/test_smoke.py`
- `.planning/V2-RENDER-PIPELINE.md` (§3 motores, §7 prompting, §10 fuentes precios, estado F1-F5)
- `.planning/REQUIREMENTS.md` (DIRQ-01..07, CRE-01), `.planning/phases/12-.../12-CONTEXT.md` (decisiones LOCKED)
- Google Cloud Blog — Ultimate prompting guide for Veo 3.1 (fórmula `[Cinematografía]+[Sujeto]+[Acción]+[Contexto]+[Estilo]`, lentes, negativos por exclusión, i2v / Ingredients / first-last frame): https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1

### Secondary (MEDIUM confidence, guías 2026 cross-referenciadas)
- Kling AI Prompting (estructura sujeto-primero, cámara al final, 5-7 elementos, negativos, motion endpoints): veed.io/learn/kling-ai-prompting-guide · ambienceai.com/tutorials/kling-prompting-guide · fal.ai/learn/devs/kling-2-6-pro-prompt-guide · magichour.ai/blog/kling-30-reference-guide
- Runway Gen-4 (describe movimiento no apariencia; sin negativos; simple; una moción primaria): help.runwayml.com Gen-4 Video Prompting Guide (403 a fetch directo, contenido vía WebSearch) · imagine.art/blogs/runway-gen-4-5-prompt-guide
- Continuidad / last-frame chaining / character lock: magichour.ai/blog/how-to-keep-characters-consistent-in-ai-video · renderfire.com/blog/character-consistency-ai-generation · aimagicx.com (clip chaining, 3-10s)
- Convenciones de videoclip (energía→cámara/cortes): soundonsound.com/techniques/video-editing-music-promos · filtergrade.com/6-camera-movements-for-your-next-music-video

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | El esquema de input de fal para i2v acepta un campo `image_url` (nombre exacto varía por modelo) | DIRQ-05 / render_client | Bajo — el camino real ya está aislado y los modelos son configurables por env; el **plan** dry-run no depende del nombre exacto |
| A2 | El campo persistido nuevo para la biblia (`visual_bible_json` en `Song`) requiere migración de esquema DB | Runtime State / DIRQ-01 | Medio — si la persistencia es vía SQLAlchemy/columna, el planner debe incluir tarea de migración; verificar `schemas.py`/`models` antes |
| A3 | El vocabulario concreto de cámara por nivel de energía (push-in/handheld/whip) es aceptable para el usuario | DIRQ-04 | Bajo — marcado "Claude's Discretion" en CONTEXT.md; ajustable sin romper tests |
| A4 | 8-15 shots repartidos por secciones de letra es la densidad correcta sin key | DIRQ-03 | Bajo — rango dado explícitamente en CONTEXT.md/REQUIREMENTS |

## Open Questions

1. **¿Dónde se persiste la biblia visual?**
   - Sé: `onboarding_ai` ya escribe campos JSON en `Song` (`director_answers_json`, etc.).
   - No sé: si hay que añadir columna `visual_bible_json` (migración) o anidarla en `director_answers_json` (sin migración).
   - Recomendación: el planner debe leer `backend/app/schemas.py` y el modelo `Song` para decidir; **preferir anidar** en un JSON existente si evita migración, salvo que se quiera consultar la biblia por separado.

2. **¿Modelo i2v distinto al t2v en fal?**
   - Sé: `PROVIDERS[*].fal_model` apunta hoy a endpoints `text-to-video`.
   - No sé: si i2v usa otro endpoint (p.ej. `.../image-to-video`).
   - Recomendación: añadir `fal_model_i2v` configurable por env; usarlo solo cuando hay `image_url`. No bloquea dry-run.

3. **¿Añadir `prompt_veo` como cuarto campo de prompt?**
   - Sé: hoy hay `prompt_generic/runway/kling`; `veo3` usa `prompt_generic` (`render_client` línea 52).
   - Recomendación: el tuning Veo (cámara-primero) difiere del genérico; añadir `prompt_veo` opcional y mapear `veo3*` a él en `PROVIDERS`. Aditivo, no rompe F3/F5.

## Environment Availability

> F6 es código/datos en local sin dependencias externas en CI. Camino real (no F6) usaría FAL_KEY/OpenAI.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python + pytest | Tests F6 | ✓ (asumido, repo activo) | — | — |
| OPENAI/ANTHROPIC key | Biblia/shots vía LLM (opcional) | — (no requerido en CI) | — | **Heurística local** (obligatoria, ya es el patrón) |
| FAL_KEY | i2v real (DIRQ-05), reroll real (DIRQ-07) | — (no requerido) | — | **dry-run** (plan verificable sin gastar) |
| ffmpeg / librosa / yt-dlp | F1/F5 (no F6) | — | — | No tocados por F6 |

**Missing dependencies with no fallback:** Ninguna que bloquee F6 (todo dry-run/heurístico).
**Missing dependencies with fallback:** LLM→heurística; FAL→dry-run. Ambos ya implementados en el repo.

## Metadata

**Confidence breakdown:**
- Estructura/tuning de prompt por motor: HIGH — docs oficiales Veo + guías 2026 múltiples y concordantes para Kling/Runway.
- Arquitectura de código (dónde tocar): HIGH — leído del repo, puntos de extensión claros y aditivos.
- Continuidad last-frame chaining: HIGH (concepto) / MEDIUM (esquema exacto fal i2v, ver A1/Q2).
- Mapeo energía→cámara: MEDIUM — convención de videoclip + diseño propio; "Claude's Discretion".
- Pitfalls y validación: HIGH — derivados de docs + forma de datos real del repo.

**Research date:** 2026-05-29
**Valid until:** ~2026-06-28 (motores de vídeo-IA evolucionan rápido; revalidar esquemas fal/versiones de motor en ~30 días)
