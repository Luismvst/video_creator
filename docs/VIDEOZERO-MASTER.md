# VideoZero — Documento maestro de producto (v1 · **letra primero**)

> **Mantra:** *VideoZero es un director creativo guiado por la letra.*  
> **Propósito:** Base única para visión, MVP, arquitectura, flujo creativo, modelo de datos, riesgos y GSD.

---

## 0. Qué cambia respecto a v0.x

| Antes (v0.x) | Ahora (v1) |
|----------------|------------|
| “Canción + audio” como narrativa central | **Letra** como fuente de verdad creativa; audio **opcional** para refinar tiempo, no para arrancar el producto |
| Fase 2 = análisis DSP prioritario | **Inteligencia de letra + estructura + dirección** primero; **análisis musical pesado (BPM, onsets, curvas)** = **post-MVP / modo Pro** |
| OPS centrado en pista | **Declaración de derechos sobre la letra** (obligatoria antes de generar documentos/planos); derechos de **audio** solo si hay archivo |

---

## 1. North Star

**VideoZero** guía al usuario desde la **letra** (y metadata mínima) hasta un **paquete de dirección coherente** para videoclips con IA: interpretación, preguntas de director, rutas creativas, biblia visual, treatment, timeline anclada a **bloques de letra y secciones**, escenas, shot list, prompts por proveedor, plan de generación y revisión — **sin** tratar cada plano como un prompt aislado.

**Audio:** opcional. Si existe, sirve para **duración**, referencia de “feel” y (más adelante) sincronía; **no** es requisito del camino feliz.

**No promete en v1:** render por API; análisis DSP completo; alineación letra–voz perfecta.

**Sí promete en v1:** coherencia narrativa/visual **nacida de la letra** y de las decisiones de dirección capturadas; exports útiles para Runway/Veo/Kling/etc.

---

## 2. Usuario y caso de uso inicial

- **Primario:** cantautor / letras muy visuales; el videoclip debe “leer” la letra, no decorarla con clips random.
- **Secundario:** equipo que recibe **treatment + shot list + prompt packs** sin entrar en la app.

**Éxito observable (MVP):** en una sesión el usuario puede (1) crear proyecto y pegar letra, (2) definir o revisar **estructura** (secciones / bloques), (3) completar **dirección guiada** y bloquear “Creative Lock”, (4) exportar **treatment + biblia + timeline + shot list + prompts** sin haber subido audio (opcional).

---

## 3. Principios (invariantes)

1. **La letra manda.** Preguntas, rutas, biblia y timeline deben poder justificarse citando **líneas o bloques**.
2. **La unidad atómica sigue siendo el Shot**, pero hereda de **Line / Block / Section / CreativeLock / VisualBible**, no de un prompt suelto.
3. **Reloj del proyecto:** (a) duración objetivo **manual** (segundos o “corto/medio/largo”) y/o (b) audio opcional con **duración por ffprobe** en fase ligera; **no** exigir BPM/onsets en v1.
4. **Referencias → atributos**; nunca copiar obra o artista identificable en prompts finales.
5. **Humano en el circuito:** edición de estructura de letra, lock explícito antes de explosión de planos.

---

## 4. MVP (v1) — alcance

### Incluye

| # | Capacidad |
|---|-----------|
| 1 | Workspace por proyecto de videoclip |
| 2 | **Letra** obligatoria (pegar/subir); **audio** opcional |
| 3 | Metadata básica (título, artista, idioma, mood) |
| 4 | **Estructura**: secciones vinculadas a bloques/líneas (editable) |
| 5 | **Reloj**: `target_duration_seconds` opcional (usuario) + si hay audio, duración detectada (ffprobe, fase ligera) |
| 6 | Análisis de letra: líneas/bloques, imágenes, símbolos, lecturas interpretativas (LLM asistido, editable) |
| 7 | Alineación **opcional** línea ↔ tiempo (si el usuario tiene timestamps; si no, posición relativa a sección) |
| 8 | Intake creativo + motor de dirección + rutas + **Creative Lock** |
| 9 | Visual Bible + Treatment |
| 10 | Timeline por **secciones de letra** + scene cards + shot list |
| 11 | Prompt compiler (genérico + Runway + Kling por defecto) |
| 12 | Generation plan + checklist + matriz de revisión |
| 13 | Export Markdown / CSV / JSON / prompt packs |
| 14 | **OPS:** confirmación de derechos sobre **letra** antes de pipeline generativo; si hay audio, confirmación adicional antes de cualquier procesamiento de archivo de audio |

### Fuera de v1 (explícito)

- BPM/onsets/segmentación automática “científica”, curvas de energía densas (roadmap **Audio Pro**).
- Render vídeo por API unificado.
- EDL/FCPXML (roadmap).
- Colaboración realtime.

---

## 5. Flujo UX (letra primero)

1. **Letra & metadata** — pegar letra, metadata, declaración derechos letra.  
2. **Estructura** — secciones ↔ bloques/líneas.  
3. **Reloj** — duración objetivo (opcional); audio opcional + derechos si aplica.  
4. **Intake creativo** — referencias → atributos.  
5. **Dirección** — preguntas + rutas + **Lock**.  
6. **Plan** — timeline → escenas → shots (tablas).  
7. **Prompts** — compilar por proveedor.  
8. **Revisión & export**.

---

## 6. Arquitectura lógica

```
Ingest (lyrics required, audio optional)
  → StructureEngine (sections ↔ lyric blocks)
  → LyricsAnalysis (LLM, /prompts versionados)
  → Optional: LightAudio (ffprobe duration only, if file)
  → CreativeResearch + DirectorDecisions (versioned)
      → VisualBible + Treatment
          → TimelinePlanner (lyric/section clock)
          → ScenePlanner → ShotList
              → PromptCompiler(provider)
                  → GenerationPlan + ReviewMatrix → Export
```

**Audio Pro branch (posterior):** librosa features, beat grid, energy curve → alimentan timeline como *sugerencias*, no como verdad única.

---

## 7. Modelo conceptual de datos (ajustes)

- **Project**, **Song** (o **ClipWork**): `lyrics_text` requerido para pasar gates; `audio_*` opcional; `target_duration_seconds` opcional; `lyrics_rights_confirmed`, `audio_rights_confirmed` (solo relevante si hay audio).
- **LyricSection**: id, orden, etiqueta (verso/estribillo/custom), `line_id` ranges o FK a bloques.
- Resto (VisualBible, Treatment, Scene, Shot, PromptPack, …) como en v0.2, con timeline referenciando **secciones de letra** antes que “segmentos DSP”.

---

## 8. Stack técnico

Sin cambio sustancial: Next.js + FastAPI + SQLite/Postgres + `/prompts` versionados. **Workers + librosa** se posponen al modo Audio Pro.

---

## 9. Riesgos y calidad

- **Letra ajena / copyright:** OPS explícito; no asumir licencia.
- **Audio opcional:** reduce superficie legal, no la elimina si el usuario sube samples.
- **Anti-collage:** cada escena cita ancla de letra o decisión de lock; límite de planos por sección.

---

## 10. Decisiones pendientes

1. ¿Renombrar entidad `Song` → `ClipWork` / `LyricProject` en código (cosmético + claridad)?
2. ¿Un solo checkbox legal vs letra/audio separados? (v1 recomienda **separados** si hay audio.)
3. Idioma UI / treatment bilingüe.
4. Límites de tamaño si se mantiene upload opcional.

---

## 11. GSD — próximo trabajo

1. Actualizar `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md` a esta línea.  
2. Reordenar fases: **Lyrics & structure** antes que cualquier DSP.  
3. Ajustar UI/API a gates “letra primero”.  
4. `/gsd-plan-phase` según nuevo roadmap.

---

*v1 · letra primero — 2026-05-13*
