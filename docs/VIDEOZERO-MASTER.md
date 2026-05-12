# VideoZero — Documento maestro de producto (v0.2)

> **Propósito:** Base única para visión, MVP, arquitectura, flujo creativo, modelo de datos, riesgos y siguiente paso GSD. Sustituye/condensa el mega-prompt inicial en algo accionable.

---

## 0. Diagnóstico del prompt original (sin perder intención)

| Área | Qué funcionaba | Qué diluía el foco |
|------|----------------|-------------------|
| **Visión** | Pipeline Song → … → Edit claro; “la unidad no es el prompt” | Mezcla rol de 10 expertos con backlog de 16 módulos en un solo bloque |
| **MVP** | “Sin API de vídeo día 1” bien acotado | Lista de exportables larga sin prioridad ni orden de lectura |
| **Arquitectura** | Stack razonable (Next + FastAPI) | Módulos numerados como si ya existieran; falta contrato entre capas |
| **Creativo** | Coherencia letra/música/emoción | Poco explícito sobre *anti-collage* y revisión humana |
| **Legal** | Mención de riesgos | Sin políticas operativas (referencias, estilo de terceros, contenido sensible) |
| **Datos** | Alineación línea–timestamp | Sin esquema conceptual único de entidades |

**Decisiones implícitas a explicitar:** idioma del producto vs idioma de la canción; si el usuario edita siempre antes de “congelar” dirección; qué es obligatorio vs opcional en v1; límites de duración/tamaño de audio.

---

## 1. North Star

**VideoZero** guía a músicos y creadores no técnicos desde **canción + letra (+ referencias opcionales)** hasta un **paquete de producción coherente**: interpretación, dirección creativa, biblia visual, timeline, escenas/planos, prompts por proveedor, plan de generación y plan de montaje — sin tratar cada plano como un prompt aislado.

**No promete en v1:** render automático de videoclip completo vía API unificada.

**Sí promete en v1:** reducir caos y collage; hacer que cada plano **herede** contexto superior (letra, sección, tiempo, emoción, reglas de continuidad, proveedor objetivo).

---

## 2. Usuario y caso de uso inicial

- **Primario:** cantautor / letras muy visuales, narrativa poética, imágenes recurrentes (carretera, memoria, ciudad, etc.).
- **Secundario (post-MVP):** productor que quiere treatment + shot list para equipo externo.

**Éxito observable (MVP):** en una sesión el usuario puede (1) subir audio + letra, (2) revisar/alinear líneas con tiempo, (3) completar un flujo guiado de dirección, (4) exportar al menos **treatment + biblia visual + shot list + prompt pack** listos para llevar a Runway/Veo/etc. manualmente.

---

## 3. Principio de producto (invariantes)

1. **La unidad atómica no es “un prompt”.** Es un **Shot** anclado a jerarquía: Song → Section → Scene → Shot.
2. **Nada downstream sin inputs validados:** letra estructurada + ventana temporal mínima + decisiones de dirección congeladas (versionadas).
3. **Referencias → atributos**, nunca copia literal de obra/artista identificable en prompts finales.
4. **Humano en el circuito:** alineación letra–audio editable; aprobación de “ruta creativa” antes de explosión de planos.

---

## 4. MVP (v1) — alcance cerrado

### 4.1 Incluye

| # | Entregable / capacidad | Notas |
|---|------------------------|--------|
| 1 | Proyecto / workspace por canción | Versionado ligero de “snapshots” de dirección |
| 2 | Ingesta: audio + letra (pegar/subir) + metadata básica | Título, artista, idioma, mood objetivo |
| 3 | Análisis de audio **heurístico** | Duración, BPM aprox, onsets, energía por tramo, segmentación tentativa, curva de intensidad |
| 4 | Análisis de letra | Líneas, bloques, imágenes/símbolos/lugares/personajes, lecturas interpretativas (propuestas, no dogma) |
| 5 | **Alineación letra ↔ tiempo** | Tabla editable: `line_id`, texto, start, end, section, intensity, notas |
| 6 | Agente de **investigación creativa** (preguntas + referencias) | Traducción a atributos estéticos |
| 7 | **Director Decision Engine** | Preguntas guiadas, opciones concretas, todo persistido como constraints |
| 8 | **Rutas creativas** (varias) + elección o mezcla | A/B/C… con trade-offs en lenguaje natural |
| 9 | **Visual Bible** + **Treatment** | Documentos exportables |
| 10 | **Timeline por secciones** + **Scene cards** | Bloques con letra asociada, emoción, objetivo narrativo, transiciones |
| 11 | **Shot list** + **prompts por plano** + **Prompt Compiler** | Perfil genérico + ≥2 proveedores concretos en v1 (elegir cuáles en decisión pendiente) |
| 12 | **Generation plan** + **checklist** + **matriz de revisión** | Orden sugerido, dependencias, criterios PASS/FAIL por plano |
| 13 | **Export engine** | Prioridad v1: `markdown` + `json` + `csv` shot list + `prompt_pack` por proveedor seleccionado |

### 4.2 Fuera de v1 (explícito)

- EDL / FCPXML / Premiere / Resolve (roadmap).
- Generación de vídeo por API desde la app.
- Alineación automática “perfecta” letra–voz (solo asistida + manual).
- Colaboración multiusuario en tiempo real.

### 4.3 Criterios de utilidad del MVP

- Un plano puede reconstruirse **solo leyendo** Visual Bible + Scene + línea asociada + timestamp.
- El usuario puede explicar el videoclip a un tercero usando solo **treatment + timeline**.
- La shot list es importable mentalmente en hoja de cálculo (CSV limpio, columnas estables).

---

## 5. Flujo de usuario (UX guiada)

Fases sugeridas en UI (nombres internos):

1. **Song Setup** — audio, letra, metadata.
2. **Structure** — revisar segmentación audio + bloques de letra.
3. **Align** — tabla línea–tiempo (asistencia opcional).
4. **Creative Intake** — referencias y “vibes” (traducidos a atributos).
5. **Direction** — preguntas + rutas creativas + congelar “Creative Lock”.
6. **Plan** — timeline → escenas → shot list (editable tipo tabla).
7. **Prompts** — compilar por proveedor; ver diff vs biblia.
8. **Generate & Review** — checklist + matriz (assets subidos manualmente o links).
9. **Export** — paquete zip o lista de archivos.

---

## 6. Arquitectura lógica (módulos con contratos)

```
Ingest → AudioAnalysis + LyricsAnalysis → AlignmentStore
    → CreativeResearch + DirectorDecisions (versioned)
        → CreativeDirection + VisualBible + Treatment
            → TimelinePlanner → ScenePlanner → ShotListGenerator
                → PromptCompiler(provider) → GenerationPlan + ReviewMatrix
                    → ExportEngine
```

- **Analysis** no llama a LLM con prompts gigantes embebidos: lee `/prompts` versionados (id, version, purpose, input/output schema, ejemplos).
- **Planning** consume solo schemas validados (Pydantic/TS types espejo).
- **Compiler** es puro: `Shot + VisualBible + ProviderProfile → ProviderPrompt`.

---

## 7. Modelo conceptual de datos (mínimo viable)

| Entidad | Campos clave (conceptual) |
|---------|---------------------------|
| **Project** | id, name, created_at, locale |
| **Song** | audio_uri, duration_s, bpm_est, language, genre_tags |
| **LyricDocument** | raw_text, normalized_lines[] |
| **LyricLine** | line_id, text, block_id, order |
| **AudioSegment** | seg_id, start, end, label_tentative, energy |
| **LineAlignment** | line_id, start, end, section_override, emotional_intensity, visual_notes |
| **CreativeSession** | id, status (draft/locked), answers JSON, chosen_routes[] |
| **VisualBible** | characters[], locations[], palette, camera_grammar, textures, continuity_rules, no_gos |
| **Treatment** | markdown, summary_one_liner |
| **TimelineBlock** | block_id, start, end, section, lyric_line_ids[], narrative_goal, primary_visual, in_transition, out_transition, edit_pace |
| **Scene** | scene_id, timeline_block_ids[], mood, location_ref, character_refs[] |
| **Shot** | shot_id, scene_id, t_start, t_end, duration_s, lyric_ref, action, subject, camera, lens_look, lighting, location, mood, continuity_constraints, provider_hint, prompt_core, negative_prompt, ref_assets[], review_criteria[] |
| **PromptPack** | provider, shots[] compiled prompts |
| **GenerationPlan** | ordered_steps[], dependencies, notes (i2v vs t2v) |
| **ReviewItem** | shot_id, criteria_scores, prompt_variants[] |
| **ExportBundle** | list of artifacts + checksum |

---

## 8. Stack técnico (por fases, sin overengineering)

**Fase A — MVP**

- **Frontend:** Next.js, React, TypeScript, Tailwind, shadcn/ui, estado local (Zustand o equivalente), tablas editables, preview Markdown, export.
- **Backend:** FastAPI, Pydantic, SQLModel/SQLAlchemy, SQLite (dev) / Postgres (prod), almacenamiento local (MVP) con interfaz para S3/R2 después.
- **Workers:** cola async para análisis de audio (Celery/RQ/Arq/Dramatiq + Redis si hace falta).
- **Tiempo real progreso:** SSE o WebSocket para jobs largos.
- **Audio:** ffmpeg + librosa (normalización, BPM, onsets, energía, segmentación básica).

**Fase B — post-MVP**

- Separación stems (demucs/spleeter), Whisper/WhisperX solo como **asistencia** de alineación.
- Capa `VideoProvider` (TypeScript o Python con contrato compartido vía OpenAPI + tipos generados).

---

## 9. Capa de proveedores de vídeo (futuro cercano)

Interfaz lógica (lenguaje agnóstico):

- `name`, `capabilities` (duración max, i2v, t2v, referencia personaje, etc.)
- `compilePrompt(ShotPromptInput) → ProviderPrompt`
- Opcional: `submitGeneration`, `getJobStatus`, `downloadResult`

**Regla:** el núcleo del producto solo conoce **ShotPromptInput** canónico; cada proveedor es un adaptador.

---

## 10. Riesgos legales y creativos (operativos)

1. **Música:** el usuario declara derechos o uso autorizado; la app no asume licencia; opcional: checkbox + texto legal corto.
2. **Imagen/personas:** consentimiento explícito si fotos de personas reales; no deepfake de terceros sin permiso.
3. **Referencias:** UI copy claro — “inspiración en estilo” ≠ copiar obra reconocible; el compilador debe **sustituir nombres propios** por descriptores (iluminación, grain, lente, paleta).
4. **Contenido sensible:** políticas de rechazo/soft-warning en narrativas violentas, menores, etc. (definir lista mínima v1).
5. **Salida de modelos:** watermark/terms del proveedor; no revender prompts como “plantillas oficiales” de terceros.

---

## 11. Calidad, coherencia y anti-collage

**Reglas de generación (para LLM interno):**

- Cada escena debe citar **al menos una ancla** (línea de letra, golpe musical, o decisión de dirección).
- Máximo N planos por bloque temporal (N configurable; default conservador).
- **Continuidad:** lista explícita “must match previous shot” cuando aplique.
- **Variación controlada:** cambios de look solo en puntos de inflexión musicales o narrativos acordados.

**Matriz de revisión (ejemplo de criterios por plano):**

- Coherencia letra / Coherencia biblia / Continuidad personaje / Movimiento / Emoción / Utilidad en montaje / Artefactos IA.

---

## 12. Exportaciones — prioridad v1

| Artefacto | Formato |
|-----------|---------|
| Creative brief / preguntas | `.md` |
| Visual bible | `.md` |
| Treatment | `.md` |
| Timeline | `.md` |
| Shot list | `.csv` + `.json` |
| Prompt packs | `.md` por proveedor + `json` opcional embebido |
| Generation checklist + review matrix | `.md` + `.csv` |
| Edit plan | `.md` |

---

## 13. Decisiones pendientes (para siguiente iteración contigo)

1. **Idioma UI** por defecto y si el treatment puede bilingual automático.
2. **Proveedores** concretos para los 2 perfiles del MVP además de “generic cinematic”.
3. **Límite** de duración de canción y tamaño de archivo en v1.
4. **Modelo de negocio** (local-only vs cloud) — afecta storage y LLM keys.
5. **Nivel de literalidad** default (literal vs simbólico) y si se fuerza por sección.

---

## 14. Próximo paso GSD (cuando quieras ejecutar herramientas)

1. Ejecutar **`/gsd-new-project`** (o `--auto` pegando este doc) para generar `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`.
2. Opcional antes: **`/gsd-explore`** solo si quieres desbloquear decisiones de la §13 sin escribir código.
3. Fase 1 recomendada en roadmap: **vertical slice** — un proyecto demo end-to-end con export real y tablas editables, sin integración API de vídeo.

---

*Documento generado como iteración del master prompt inicial + plan de trabajo acordado. Versión v0.2.*
