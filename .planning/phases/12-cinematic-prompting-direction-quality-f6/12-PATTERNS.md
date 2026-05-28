# Fase 12: Cinematic prompting & direction quality (F6) - Mapa de Patrones

**Mapeado:** 2026-05-29
**Archivos analizados:** 7 (5 a modificar, 1 nuevo posible, 1 lote de tests)
**Análogos encontrados:** 7 / 7 (todo tiene análogo dentro del propio repo — esta fase **eleva calidad**, no inventa categorías nuevas)

> Regla rectora de la fase (de CONTEXT.md, NO negociable): **stdlib + urllib** para LLM,
> **degradación elegante sin API key**, **helpers puros testeables** separados del I/O,
> **sin imports pesados a nivel módulo**, y **no romper la forma de segmento** que consume F3/F5
> (`index/start_sec/end_sec/duration_sec/shot/prompt_generic/prompt_runway/prompt_kling/source`).

---

## Clasificación de archivos

| Archivo (nuevo/modificado) | Rol | Flujo de datos | Análogo más cercano | Calidad del match |
|----------------------------|-----|----------------|---------------------|-------------------|
| `backend/app/prompt_compile.py` (MOD) | utility / transform de texto | transform (shots → prompt por capas) | sí mismo (función fina actual) + estructura de `render_client.provider_prompt` | exacto (extender en sitio) |
| `backend/app/onboarding_ai.py` (MOD/EXT) | service (dirección/biblia) | LLM+fallback heurístico (request-response) | sí mismo (`build_onboarding_package`) + `lyrics_insights_engine` | exacto |
| `backend/app/visual_bible.py` (NUEVO posible) | service (biblia visual) | LLM+fallback heurístico | `onboarding_ai.heuristic_*`/`llm_*`/`build_*` (patrón triádico) | exacto (clónico) |
| `backend/app/music_planner.py` (MOD) | service (planner temporal) | transform (segmentos + energía→cámara) | sí mismo (`_materialize`, `_split_max`, `_is_high_energy`) | exacto |
| `backend/app/render_client.py` (MOD) | service (cliente render) | request-response + dry-run (tuning + reroll por índices) | sí mismo (`provider_prompt`, `render_timeline` con `limit`) | exacto |
| `backend/app/keyframes.py` (MOD) | service (keyframes) | I/O encadenado + dry-run (init-image real) | sí mismo (`plan_keyframes` chain) + camino real fal de `render_client._fal_generate` | exacto |
| `backend/tests/test_*.py` (NUEVOS) | test | helpers puros, sin red/binarios | `test_render_client.py`, `test_music_planner.py` | exacto |

---

## Asignación de patrones por archivo

### `backend/app/prompt_compile.py` (utility, transform) — DIRQ-02 prompt por capas

**Análogo:** función actual `compile_prompt_markdown` (a sustituir/extender por compilador por capas)
y el selector de proveedor de `render_client.provider_prompt`.

**Firma actual a respetar/extender** (`prompt_compile.py:6`):
```python
def compile_prompt_markdown(shots: list[dict[str, Any]], provider: str) -> str:
```
- Consumidores: `timed_segments._materialize`-equivalente y `music_planner._materialize`
  llaman `compile_prompt_markdown([shot], "generic"|"runway"|"kling")` y guardan en
  `prompt_generic/prompt_runway/prompt_kling`. **No cambiar esos nombres de campo.**

**Patrón de branching por proveedor a heredar** (`prompt_compile.py:31-42`) — hoy frase fina:
```python
if provider == "runway":
    lines.append(f"Texto sugerido: {act} — {cam}. Continuidad: {notes}. "
                 "Evitar texto on-screen ilegible; priorizar movimiento de cámara claro.")
elif provider == "kling":
    lines.append(f"Prompt: {act}. Lente/encuadre: {cam}. Notas: {notes}. "
                 "Mantener sujeto principal estable entre cortes adyacentes cuando aplique.")
else:
    lines.append(f"Plano: {act}\n\nCámara / encuadre: {cam}\n\nContinuidad / revisión: {notes}")
```

**Qué construir (capas, CONTEXT §DIRQ-02 + §DIRQ-06):**
Orden verificable en el texto:
`[sujeto+acción de la línea] + [cámara/movimiento] + [biblia: óptica/luz/paleta/grano/DOF] + [negativos] + [aspect/duración]`.
- Recomendación: **firma nueva o ampliada** que acepte la biblia y el aspect/duración además de los shots,
  manteniendo `compile_prompt_markdown(shots, provider)` como wrapper retrocompatible (o añadir
  un parámetro opcional `bible: dict | None = None`, `aspect: str = "16:9"`, `duration_sec: float | None = None`
  con defaults → no rompe a los callers actuales).
- Tuning por proveedor (DIRQ-06): Kling sujeto-primero + cámara explícita; Veo descriptivo cinematográfico;
  Runway movimiento claro + evitar texto on-screen. Reusar el `if/elif/else` por `provider` de arriba.
- **Pureza:** sigue siendo función pura de strings → fácilmente testeable (substring de paleta/óptica/negativos/aspect).

---

### `backend/app/onboarding_ai.py` (service, LLM+fallback) — DIRQ-01 biblia / DIRQ-03 shots ricos

**Análogo:** el propio módulo. Patrón triádico canónico del repo: `heuristic_*` (puro) + `llm_*`
(urllib) + `build_*` (orquestador con degradación). **Replicar este patrón, no inventar otro.**

**Config OpenAI compartida** (importar, no duplicar) — de `lyrics_insights_engine.py:121-130`:
```python
def _openai_api_key() -> Optional[str]:
    return os.getenv("VIDEOZERO_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
def openai_configured() -> bool:
    return bool(_openai_api_key())
def _openai_model() -> str:
    return os.getenv("VIDEOZERO_OPENAI_MODEL", "gpt-4o-mini")
```
Ya importados en `onboarding_ai.py:10`:
```python
from .lyrics_insights_engine import _openai_api_key, _openai_model, openai_configured
```

**Patrón LLM vía urllib (call + parseo defensivo)** — `onboarding_ai.py:175-244`:
```python
body = json.dumps({
    "model": _openai_model(),
    "temperature": 0.45,
    "response_format": {"type": "json_object"},
    "messages": [
        {"role": "system", "content": "Eres director creativo de videoclips. Respondes únicamente con JSON válido."},
        {"role": "user", "content": user},
    ],
}).encode("utf-8")
req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    ...
    return None, f"OpenAI HTTP {e.code}: {detail}"
except Exception as e:  # noqa: BLE001
    return None, f"OpenAI: {e}"
# limpiar fences ```json ... ``` antes de json.loads (líneas 213-221)
```

**Patrón de degradación (orquestador)** — `onboarding_ai.build_onboarding_package:247-269`:
```python
if prefer_llm and openai_configured():
    pkg, err = llm_onboarding_package(...)
    if pkg:
        return pkg, "Dirección generada con IA (OpenAI)."
    h = heuristic_onboarding_package(...)
    return h, f"Heurística local (IA no disponible o falló: {err or 'motivo desconocido'})."
h = heuristic_onboarding_package(...)
...
return h, "Heurística local (modo heurístico o sin IA)."
```

**Fallback heurístico (shots por defecto)** — HOY solo 2 shots (`onboarding_ai.py:119-132`).
DIRQ-03 pide **8–15 shots con intención narrativa**, repartidos por secciones de letra.
- Reusar `suggest_section_spans(lyrics_text)` (`onboarding_ai.py:17-44`) que ya parte la letra en
  estrofas (label/kind/start_line/end_line) para repartir shots por sección sin key.
- Mantener compatibilidad de shot: `slug/camera/action/notes` + nuevos opcionales `intent`, `shot_size`.

**Biblia visual (DIRQ-01) — campos estructurados a producir** (CONTEXT §DIRQ-01):
`subject`, `world`, `palette`, `optics` (p.ej. 35mm/85mm), `light_rule`, `grain_dof`,
`style_attributes[]` (atributos derivados, **nunca** nombres de obra/artista), `negatives[]`.
- Vive junto a `director_answers_json` (ya existe en el patch de `build_onboarding_package`).
  **Extender, no duplicar:** añadir clave nueva (p.ej. `visual_bible_json`) al dict que devuelve
  `build_onboarding_package`/`heuristic_onboarding_package`, persistida y reutilizada en TODOS los segmentos.
- Regla anti-copyright ya presente en el system-prompt LLM (`onboarding_ai.py:172`): mantenerla literal.

---

### `backend/app/visual_bible.py` (NUEVO posible) — Discreción: módulo propio vs extender onboarding_ai

**Análogo:** clonar el patrón triádico de `onboarding_ai.py` (`heuristic_` + `llm_` + `build_`).
Si se opta por módulo separado:
- `def heuristic_visual_bible(lyrics_text, brief, *, title, mood) -> dict[str, Any]` (PURO, desde brief/letra).
- `def llm_visual_bible(...) -> tuple[Optional[dict], Optional[str]]` (urllib, mismo molde que `llm_onboarding_package`).
- `def build_visual_bible(..., prefer_llm) -> tuple[dict, str]` (degradación idéntica).
- Importar config OpenAI de `lyrics_insights_engine` (no redefinir).
- **No imports pesados a nivel módulo** (solo `json/os/re/urllib`).

> Decisión Discreción (CONTEXT §Claude's Discretion): el planner puede elegir extender `onboarding_ai`
> en lugar de crear módulo. El patrón a copiar es idéntico en ambos casos.

---

### `backend/app/music_planner.py` (service, transform) — DIRQ-04 modulación por energía

**Análogo:** el propio módulo. Ya consume secciones/energía y trocea más en alta energía.
F6 añade **vocabulario de cámara + shot_size** que escalan con energía, inyectados en el segmento.

**Helper de energía a reusar** — `music_planner._is_high_energy:63-70`:
```python
def _is_high_energy(t, sections, threshold) -> bool:
    if not sections or threshold is None:
        return False
    for sec in sections:
        if float(sec["start_sec"]) <= t < float(sec["end_sec"]):
            return float(sec.get("mean_energy", 0.0)) > threshold
    return False
```
y `_section_energy_threshold:56-61` (mediana de `mean_energy`). El `_split_max:73-105` ya usa esto.

**Punto de inyección: `_materialize:108-139`** — donde se construye cada segmento. Aquí se añade
el vocabulario de cámara/shot_size derivado de la energía del intervalo `[s, e]`:
```python
seg: dict[str, Any] = {
    "index": i + 1,
    "start_sec": round(s, 2),
    "end_sec": round(e, 2),
    "duration_sec": round(e - s, 2),
    "shot": dict(shot),
    "line_indices": li,
    "source": "music",
    "prompt_generic": compile_prompt_markdown([shot], "generic").strip() if shot else "",
    "prompt_runway": compile_prompt_markdown([shot], "runway").strip() if shot else "",
    "prompt_kling": compile_prompt_markdown([shot], "kling").strip() if shot else "",
}
```
- **F6:** antes de compilar prompts, enriquecer `shot` (o el segmento) con `camera_move`/`shot_size`
  según `_is_high_energy(s, sections, threshold)`: alta energía → push-in/handheld/whip + plano más cerrado;
  baja → plano sostenido. Así el prompt por capas (compilador) recibe ya la cámara modulada.
- **Degradación (CONTEXT §DIRQ-04):** sin audio (rama heurística, `_enforce_max_clip:187-209`) → perfil
  **neutro** de cámara. No romper la rama solo-letra ni `plan_timeline:212-252`.
- **Helper puro nuevo recomendado:** `def camera_for_energy(high: bool) -> dict[str, str]` (vocabulario
  por nivel) → testeable sin audio. (Discreción: vocabulario concreto libre.)
- **Forma de segmento intacta:** los campos de F3/F5 no se tocan; `camera_move/shot_size` van dentro de
  `shot` o como extras opcionales.

---

### `backend/app/render_client.py` (service, request-response + dry-run) — DIRQ-06 tuning / DIRQ-07 reroll

**Análogo:** el propio módulo. Ya tiene selección de prompt por proveedor y `limit`.

**Selector de prompt por proveedor** — `render_client.provider_prompt:82-85`:
```python
def provider_prompt(segment: dict[str, Any], provider: str) -> str:
    field = _provider_cfg(provider)["prompt_field"]
    return (segment.get(field) or segment.get("prompt_generic") or "").strip()
```
Mapeo proveedor→campo en `PROVIDERS` (`render_client.py:43-69`): `kling→prompt_kling`,
`runway→prompt_runway`, `veo3/veo3_fast/wan→prompt_generic`. **El tuning por proveedor (DIRQ-06) se
materializa aguas arriba en el compilador**, llenando esos `prompt_*`. `render_client` solo selecciona.

**Reroll dirigido (DIRQ-07)** — extender el patrón `limit` de `render_timeline:186-236`:
```python
to_render = segments[:limit] if limit else segments
...
results = [render_segment(s, ...) for s in to_render]
```
- **F6:** añadir selección por índices o por flag `needs_reroll`. Patrón a seguir (mismo estilo
  declarativo, sin tocar la firma existente — parámetro nuevo opcional):
  `only_indices: Optional[list[int]] = None` →
  `to_render = [s for s in segments if s.get("index") in set(only_indices)]` (o por `s.get("needs_reroll")`).
- **Reusar el resto:** los clips no marcados se conservan (no regenerar). La estimación de coste
  (`estimate_render_cost:92-120`) y el gate (`within_budget:123-136`) deben calcularse sobre el subconjunto
  a regenerar (igual que hoy con `limit`).
- **Naming de clip estable** (`render_segment:158`): `clip_{int(idx):03d}.mp4` — mantener para que el
  reroll sobrescriba el clip correcto y `video_assembly.resolve_clip_paths` siga cuadrando.

---

### `backend/app/keyframes.py` (service, I/O encadenado + dry-run) — DIRQ-05 init-image real

**Análogo:** el propio módulo (plan de encadenado) + el camino real fal aislado de
`render_client._fal_generate:254-304` (queue API por urllib, polling, descarga).

**Plan de encadenado existente** — `keyframes.plan_keyframes:53-93`:
```python
prev_path: Optional[str] = None
for s in segments:
    ...
    items.append({"index": idx, "model": KEYFRAME_FAL_MODEL,
                  "reference_image": prev_path if chain else None,
                  "would_write": path, "has_prompt": bool(prompt)})
    if chain:
        prev_path = path
```
- Esto YA es el **plan verificable en dry-run** que pide CONTEXT §DIRQ-05 ("qué referencia a qué"):
  `reference_image` = keyframe anterior. **Mantener verificable en dry-run sin gastar.**

**Camino real a implementar (aislado tras `dry_run=False` + `FAL_KEY`)** — copiar el molde de
`render_client._fal_generate:254-304`:
```python
submit_url = f"https://queue.fal.run/{model}"
submitted = _http_json(submit_url, method="POST", key=key, body=payload, timeout=60.0)
status_url = submitted.get("status_url") or submitted.get("response_url")
# polling hasta COMPLETED / FAILED / timeout (líneas 276-289)
video_url = (result.get("video") or {}).get("url") or result.get("url")
urllib.request.urlretrieve(video_url, str(out_path))
```
- **DIRQ-05 init-image:** el camino real de keyframe i debe pasar **el keyframe i-1 (o último frame del
  clip i-1) como init-image** del image-to-video del segmento i. Reusar `reference_image` del plan.
- **Helper HTTP reusable** — `render_client._http_json:243-251` (auth `f"Key {key}"`): considerar
  extraerlo/reusarlo en keyframes para no duplicar la llamada fal (mismo gateway, misma auth).
- **No imports pesados:** solo `os/pathlib/urllib` (hoy keyframes ni siquiera importa urllib → añadir
  solo dentro del camino real, manteniendo top-level ligero).

---

### `backend/tests/test_*.py` (NUEVOS) — tests puros

**Análogos:** `test_render_client.py` y `test_music_planner.py`.

**Estilo a copiar:**
- Docstring que declara la naturaleza: `"""Tests ... Puros + dry-run: sin red ni FAL_KEY."""`
  (`test_render_client.py:1`).
- Fábricas de fixtures locales mínimas (`_segs(n, dur)` en `test_render_client.py:14-19`;
  `SHOTS`/`_timings` en `test_music_planner.py:11-23`).
- Aserciones sobre **helpers puros** y sobre el **dry-run** (sin red, sin binarios, sin FAL_KEY/OPENAI key).
- Para LLM: NO llamar a la red; testear solo el **heurístico** y el **parseo/degradación** (no hay test
  de red en el repo — mantener la suite offline).

**Tests específicos de F6 a añadir (derivados de los criterios de CONTEXT):**
- `prompt_compile`: el prompt por capas contiene substring de **paleta** y **óptica** de la biblia,
  un **bloque de negativos**, y el **aspect** — y respeta el **orden** de capas (DIRQ-02).
- `visual_bible`/`onboarding_ai`: el heurístico produce todos los campos estructurados
  (`subject/world/palette/optics/light_rule/grain_dof/style_attributes/negatives`) sin key (DIRQ-01);
  shots heurísticos ≥ 8 y ≤ 15 (DIRQ-03).
- `music_planner`: alta energía → `camera_move`/`shot_size` más intensos que baja; sin audio → perfil
  neutro; **forma de segmento intacta** (campos F3/F5 presentes) (DIRQ-04).
- `render_client`: reroll por índices/`needs_reroll` regenera SOLO los marcados; estimación/gate sobre
  el subconjunto (DIRQ-07).
- `keyframes`: el plan dry-run encadena `reference_image[i] == would_write[i-1]` (DIRQ-05).

---

## Patrones compartidos (cross-cutting)

### Configuración LLM (OpenAI) — IMPORTAR, no duplicar
**Fuente:** `backend/app/lyrics_insights_engine.py:121-130`
**Aplica a:** `onboarding_ai.py`, `visual_bible.py` (si nuevo)
```python
_openai_api_key()  # VIDEOZERO_OPENAI_API_KEY | OPENAI_API_KEY
openai_configured()
_openai_model()    # VIDEOZERO_OPENAI_MODEL, default "gpt-4o-mini"
```

### Degradación elegante (LLM → heurístico) — patrón triádico
**Fuente:** `onboarding_ai.build_onboarding_package:247-269` (y gemelo en `lyrics_insights_engine`)
**Aplica a:** todo módulo que llame LLM en esta fase
- Siempre `heuristic_*` puro de respaldo; LLM solo mejora; devolver `(resultado, nota)` y nunca lanzar.

### Llamada HTTP por urllib + parseo defensivo
**Fuente:** `onboarding_ai.py:190-221` (OpenAI) y `render_client._http_json:243-251` + `_fal_generate:254-304` (fal)
**Aplica a:** cualquier I/O de red de la fase
- `urllib.request.Request(... method="POST")`, `try/except HTTPError/Exception`, limpiar fences ```json,
  `json.loads`, validar forma antes de devolver. Sin SDKs.

### Config por entorno con fallback numérico
**Fuente:** `render_client._f:32-39` y `keyframes._f:19-26` (idénticos)
**Aplica a:** cualquier tarifa/umbral nuevo (p.ej. shot_size por energía si parametrizable)
```python
def _f(name, default): ... # lee env, float seguro, default si vacío/ inválido
```

### Dry-run como modo por defecto, camino real aislado
**Fuente:** `render_client.render_segment:163-183`, `render_timeline:213-218`, `keyframes.plan_keyframes`
**Aplica a:** `render_client` (reroll), `keyframes` (init-image real)
- `dry_run=True` por defecto: valida + estima, no gasta, no necesita key. `dry_run=False`+`FAL_KEY` → real.

### Forma de segmento canónica (NO romper)
**Fuente:** `timed_segments.propose_timed_segments:58-67` y `music_planner._materialize:124-135`
**Aplica a:** `music_planner`, `prompt_compile`, `render_client`, `keyframes`
- Campos consumidos por F3/F5: `index/start_sec/end_sec/duration_sec/shot/prompt_generic/prompt_runway/prompt_kling/source`.
  Extras nuevos (`intent/shot_size/camera_move/needs_reroll/visual_bible_json`) deben ser **aditivos y opcionales**.

---

## Sin análogo

Ninguno. Todos los archivos de F6 tienen un análogo directo en el repo (la fase es de mejora de
calidad sobre módulos ya existentes, no de nuevas categorías). El planner debe **extender en sitio**
siguiendo los patrones citados, no improvisar nuevos estilos.

---

## Metadata

**Ámbito de búsqueda de análogos:** `backend/app/` y `backend/tests/`.
**Archivos escaneados (leídos íntegros):** `prompt_compile.py`, `onboarding_ai.py`, `render_client.py`,
`music_planner.py`, `keyframes.py`, `music_analysis.py`, `lyrics_insights_engine.py`, `timed_segments.py`,
`test_render_client.py`, `test_music_planner.py` + listado de `backend/tests/`.
**Fecha de extracción:** 2026-05-29.
