# VideoZero v2 — Pipeline de render automático (URL/letra → vídeo final)

> **Estado:** Propuesta (2026-05-28). Esto es un **giro de alcance**, no la continuación natural del MVP.
> El MVP v1 termina en **dirección + prompts exportables**. El "render por API" está
> marcado **Out of Scope** en `PROJECT.md` y `VIDEOZERO-MASTER.md §4`.
> Lo que se pide aquí es un **milestone v2 nuevo**, que absorbe además el "Audio Pro" diferido.

---

## 0. ¿Estaba esto en el proyecto?

**No.** El proyecto actual (v1) es un *director creativo* que entrega un **paquete de dirección**
(biblia, treatment, timeline por secciones, shot list, prompts por proveedor). Decisiones explícitas:

- `PROJECT.md → Out of Scope`: **"Render de vídeo por API desde la app en v1"** y
  **"Análisis musical pesado (BPM, onsets, curvas) en v1 — roadmap Audio Pro"**.
- `VIDEOZERO-MASTER.md §1`: *"No promete en v1: render por API; análisis DSP completo;
  alineación letra–voz perfecta."*
- El audio es **opcional** y, cuando existe, solo se usa para duración (ffprobe). No hay descarga
  desde URL, ni separación de stems, ni transcripción, ni generación de clips, ni montaje.

Lo que pides — **URL de YouTube/Spotify → extraer audio → vídeo final montado, sin front** — es
un pipeline end-to-end de generación + ensamblado. Es un **v2 (milestone nuevo)**.

**Lo que SÍ existe ya y reutilizamos** (archivos sin commitear, base de este v2):
- `backend/app/cli_session.py` — sesión por consola: letra → preguntas de dirección → segmentos con tiempo → prompts → coste.
- `backend/app/onboarding_ai.py` — construye el paquete de dirección (shots) con LLM opcional.
- `backend/app/timed_segments.py` — reparte la duración total entre planos (heurístico, sin música real todavía).
- `backend/app/video_cost_estimate.py` — estimador de coste por proveedor (placeholders configurables por env).

Es decir: **ya tenemos letra→dirección→prompts→estimación de coste en CLI.** Faltan las piezas
de audio real y de render+montaje.

---

## 1. Lo que falta (gap del MVP al "vídeo final")

| # | Capacidad faltante | Por qué hace falta |
|---|--------------------|--------------------|
| A | **Ingesta de audio desde URL** (YouTube) | Hoy no hay descarga; necesitamos el .wav/.mp3 fuente |
| B | **Separación de stems** (voz vs instrumental) | Para alinear letra con la voz limpia |
| C | **Transcripción + alineación forzada letra↔tiempo** | El corazón de la sincronía: timestamps por palabra/línea reales (no heurística) |
| D | **Análisis musical** (BPM, beats, secciones, energía) | Cortes que caen en el beat / cambios de sección |
| E | **Planner temporal anclado a música** (sustituye al heurístico) | Que cada plano dure lo que dura su frase/sección musical |
| F | **Generación de keyframes** (imagen, opcional) | Control de estilo y continuidad antes del vídeo |
| G | **Generación de vídeo por segmento** (motor IA) | Los clips reales |
| H | **Orquestación / cola / reintentos / polling** | Render asíncrono, rerolls, control de coste y fallos |
| I | **Ensamblado final** (ffmpeg: concat + mux audio original + subtítulos) | El MP4 final con la canción real pegada |
| J | **Estimación de coste previa real** (tarifas vivas + rerolls) | Tu requisito: presupuesto antes de gastar |

---

## 2. Arquitectura del pipeline (sin front, orientado a CLI/servicio)

```
ENTRADA: URL YouTube  (o)  archivo audio  (o)  solo letra + duración objetivo
   │
   ├─[A] Ingesta audio (yt-dlp → wav 44.1k) ──────────────┐
   │                                                       │ (si solo letra: saltar A–D,
   ├─[B] Stems (Demucs v4 → vocals.wav / no_vocals.wav)    │  usar timed_segments heurístico)
   │                                                       │
   ├─[C] Alineación letra↔tiempo                           │
   │     WhisperX (transcribe vocals) + forced-align       │
   │     contra la LETRA que tú pasas (source of truth)    │
   │     → line_timings: [{line, start, end}]              │
   │                                                       │
   ├─[D] Análisis musical (librosa: BPM, beat grid,        │
   │     secciones, curva de energía)                      │
   │                                                       │
   ▼                                                       ▼
[E] PLANNER TEMPORAL  ── usa line_timings + beats + secciones ──►  segmentos [{start,end,shot}]
   │   (reemplaza el reparto heurístico de timed_segments.py)
   ▼
[ DIRECCIÓN ]  onboarding_ai.build_onboarding_package(letra, brief) → biblia + shots + prompts
   │   (YA EXISTE — se enriquece con los tiempos reales)
   ▼
[ COMPILADOR DE PROMPTS por proveedor ]  (YA EXISTE: generic/runway/kling → +veo/+kling3/+wan)
   │
   ├─[F] (opcional) Keyframe por segmento  → imagen (Flux / SDXL / Nano-Banana)
   │
   ├─[G] Vídeo por segmento  → image-to-video o text-to-video (motor elegido)
   │        vía fal.ai (gateway único) o API nativa
   │
   ├─[H] Orquestador: cola, polling, reintentos, presupuesto máx, caché
   │
   ▼
[I] ENSAMBLADO (ffmpeg)
      - concat de clips en orden de timeline
      - recorte/ajuste a la duración exacta de cada segmento
      - mux del AUDIO ORIGINAL (instrumental o mezcla) sobre el vídeo
      - (opcional) subtítulos/letra quemada desde line_timings
      → SALIDA: videoclip_final.mp4
```

**Branch "solo letra"** (sin URL ni audio): se salta A–D, usa `timed_segments.py` heurístico sobre
`target_duration_seconds`, y sigue igual desde DIRECCIÓN. Útil para previsualizar coste/estilo barato.

---

## 3. Motores recomendados por paso (mayo 2026)

| Paso | Recomendado (default) | Alternativas | Notas |
|------|----------------------|--------------|-------|
| **A. Descarga audio** | `yt-dlp` (local) | `pytubefix` | Spotify **NO** sirve: cifra el audio y prohíbe descarga; su API solo da metadata + preview 30s. **Usa la URL de YouTube** del tema. |
| **B. Stems** | **Demucs v4** (`htdemucs`) local | `audio-separator`, Spleeter | Separa voz/instrumental; mejora la alineación y permite música limpia en el mux |
| **C. Alineación letra↔tiempo** | **WhisperX** (forced-align con tu letra como transcript fijo) | `stable-ts`, Replicate `force-align-wordstamps`, ElevenLabs alignment | Sub-100ms; mucho mejor que Whisper a secas en música. Esto es lo que da la **sincronía** real |
| **D. Análisis musical** | **librosa** (BPM, beats, onset, RMS energy) | `madmom`, `essentia` | Esto es el "Audio Pro" que estaba diferido |
| **E. Planner temporal** | Lógica propia (line_timings + secciones + snap a beat) | — | Reemplaza heurística de `timed_segments.py` cuando hay audio |
| **F. Keyframes (opc.)** | **Flux 1.1 Pro** o **Nano-Banana** (Gemini img) vía fal.ai | SDXL, Ideogram | Sirve para fijar estilo/continuidad y abaratar (image-to-video sale más coherente) |
| **G. Vídeo** | **Kling 3.0** ($0.10/s, calidad/precio) | **Veo 3.1** (premium, 4K+audio, $0.75/s; fast $0.15/s) · **Wan 2.6** (budget $0.05/s) · **Runway Gen-4.5** (crédito) | **Evitar Sora 2**: OpenAI lo deprecó (apaga API 24-sep-2026) |
| **Gateway** | **fal.ai** (un API → Kling/Veo/Wan/Flux, 600+ modelos) | Replicate, API nativa de cada uno | Una sola key, fácil cambiar de motor, precios competitivos |
| **LLM dirección** | **Claude (Opus/Sonnet 4.x)** o GPT | — | Ya soportado en `onboarding_ai.py` (OpenAI). Añadir Anthropic |
| **I. Montaje** | **ffmpeg** (local) | MoviePy | concat + mux + subtítulos |

---

## 4. API keys necesarias (qué pedir y dónde)

| Servicio | Para qué | Imprescindible | Dónde | Coste base |
|----------|----------|----------------|-------|------------|
| **fal.ai** | Generación de vídeo + imagen (gateway a Kling/Veo/Wan/Flux) | **Sí** (núcleo del render) | fal.ai/dashboard/keys | Pago por uso (ver §5) |
| **Anthropic** (Claude) o **OpenAI** | Dirección creativa / shots / prompts | **Sí** (al menos una) | console.anthropic.com / platform.openai.com | ~céntimos/canción |
| **(local, sin key)** yt-dlp + ffmpeg + Demucs + WhisperX + librosa | Audio in, stems, alineación, montaje | Sí (instalación) | pip/binarios | Gratis (CPU/GPU local) |
| **Replicate** *(alternativa)* | Si no quieres correr Demucs/WhisperX local → en la nube | Opcional | replicate.com | ~$0.10–0.50/canción |
| **Google AI / Vertex** *(opcional)* | Veo 3.1 nativo si no vía fal.ai | Opcional | aistudio.google.com | per-second |
| **Spotify** | **NO sirve para audio** (solo metadata). Útil solo para autocompletar título/artista | No | developer.spotify.com | Gratis |

**Mínimo para empezar:** `FAL_KEY` + (`ANTHROPIC_API_KEY` o `OPENAI_API_KEY`). El resto es local.

`.env` propuesto:
```
FAL_KEY=...
ANTHROPIC_API_KEY=...          # o OPENAI_API_KEY
VIDEOZERO_VIDEO_PROVIDER=kling # kling | veo3 | wan | runway
VIDEOZERO_KEYFRAMES=true       # generar imagen antes del vídeo
VIDEOZERO_MAX_BUDGET_USD=40    # tope duro; aborta si la estimación lo supera
VIDEOZERO_REROLL_FACTOR=1.4    # margen de regeneraciones en la estimación
```

---

## 5. Estimación de coste (canción de 3 min = 180 s)

Supuestos: 180 s de vídeo final, clips de ~6 s → ~30 segmentos, factor de reroll ×1.4
(regeneras ~40% de los clips hasta que quedan bien).

| Partida | Cálculo | Coste |
|---------|---------|-------|
| Descarga audio (yt-dlp) | local | $0.00 |
| Stems + alineación (local GPU) | local | $0.00 |
| Stems + alineación (si en Replicate) | ~$0.30 | $0.30 |
| Dirección LLM (Claude/GPT) | 1–3 llamadas | $0.05–0.40 |
| Keyframes (Flux, ~30 img, opc.) | 30 × ~$0.04 | ~$1.20 |
| **Vídeo — Wan 2.6** (budget) | 180 s × $0.05 × 1.4 | **~$12.6** |
| **Vídeo — Kling 3.0** (recomendado) | 180 s × $0.10 × 1.4 | **~$25** |
| **Vídeo — Veo 3.1 fast** | 180 s × $0.15 × 1.4 | **~$38** |
| **Vídeo — Veo 3.1 quality (4K+audio)** | 180 s × $0.75 × 1.4 | **~$189** |
| Montaje (ffmpeg) | local | $0.00 |

**Coste total por videoclip de 3 min (todo incluido):**
- **Económico (Wan):** ~$14
- **Recomendado (Kling 3.0):** ~$26–30
- **Premium (Veo 3.1 quality):** ~$190–220

> El estimador (`video_cost_estimate.py`) ya existe con tarifas por env. **Acción:** actualizar las
> tarifas a precios 2026 (Kling 0.10, Veo 0.15/0.75, Wan 0.05) y aplicar `REROLL_FACTOR`.
> La estimación se imprime **antes** de gastar y aborta si supera `MAX_BUDGET_USD`.

Fuentes de precios: ver §9.

---

## 6. Ejemplo de extremo a extremo (worked example)

**Entrada:** URL YouTube de una canción tuya de 3:00 + letra en `.txt`.

1. `yt-dlp -x --audio-format wav <URL> -o song.wav` → 180 s, 44.1 kHz.
2. `demucs song.wav` → `vocals.wav`, `no_vocals.wav`.
3. WhisperX alinea tu letra contra `vocals.wav` →
   `line_timings.json`: `[{"line":"Caía la nieve sobre el puerto","start":12.4,"end":15.8}, ...]`.
4. librosa → `bpm=92`, beat grid, 6 secciones (intro/verso/estribillo…).
5. Planner: 28 segmentos, cada uno coincide con una frase de letra y empieza en un beat.
6. `build_onboarding_package(letra, brief)` → biblia visual + shots + prompt por segmento.
7. Por cada segmento:
   - (opc.) Flux genera keyframe del shot 7 → `kf_07.png`.
   - fal.ai Kling 3.0 image-to-video(kf_07.png, prompt, dur=3.4s) → `clip_07.mp4`.
8. ffmpeg: concat 28 clips → recorte exacto a cada `[start,end]` → mux `song.wav` (mezcla original)
   → (opc.) subtítulos quemados desde `line_timings` → **`videoclip_final.mp4`**.

**Salida:** un MP4 de 3:00 con la canción real, cortes en el beat y la imagen siguiendo la letra.

Comando objetivo (la interfaz que construiríamos):
```
python -m app.render_clip --url "https://youtu.be/..." --lyrics letra.txt \
    --provider kling --keyframes --max-budget 40 --out videoclip_final.mp4
```

---

## 7. Revisión de dirección y prompting (alto nivel)

Filosofía actual (correcta, la mantenemos y la conectamos al render):

1. **La letra manda → atributos, no copia.** El prompt de cada shot deriva de línea/sección + biblia,
   nunca de "estilo de [artista]". Reglas anti-copyright ya en el cuestionario (`cli_session._run_questionnaire`).
2. **Continuidad por biblia + keyframe.** Para que 28 clips no parezcan 28 vídeos distintos:
   - Biblia visual fija (paleta, lente, grano, sujeto, mundo) inyectada en TODOS los prompts.
   - **Keyframe encadenado:** usar el último frame del clip anterior como referencia de imagen del siguiente
     (image-to-video) → coherencia de personaje/escena. Esto es lo que evita el "collage".
3. **Prompt por capas** (plantilla por proveedor):
   `[Sujeto/acción de la línea] + [encuadre y movimiento de cámara] + [biblia: luz/paleta/lente/grano]
   + [negativos] + [duración/aspect]`. Kling/Veo responden mejor con cámara explícita y un sujeto claro.
4. **Ritmo dirigido por música:** intensidad de movimiento de cámara y nº de cortes escalan con la
   curva de energía (D). Estribillo = más movimiento; intro/puente = planos sostenidos.
5. **Humano en el lock (opcional):** mantener el "Creative Lock" del MVP como gate antes de gastar en
   render. Modo `--auto` lo salta para tu uso personal.
6. **Detalle fino se itera con la API:** versión 1 = plantillas; luego A/B de prompts por proveedor,
   negativos afinados, y reroll dirigido (solo regenerar los shots marcados, no todo).

---

## 8. Plan de implementación (fases v2)

> Recomendación GSD: abrir milestone **v2 "Render"** y reordenar como fases. Cada fase es ejecutable
> sola y deja valor.

- **v2-F1 · Ingesta + alineación de audio** (A,B,C,D): URL/archivo → `line_timings.json` + análisis musical.
  *Entregable:* comando que dado URL+letra produce los tiempos reales. Sin coste de API de vídeo.
- **v2-F2 · Planner temporal real** (E): sustituye heurística por tiempos de música; enriquece shots.
- **v2-F3 · Cliente de render + estimador real** (G,J,H): fal.ai, un solo segmento → clip; estimación
  previa con tope de presupuesto. *Gate de coste antes de escalar.*
- **v2-F4 · Keyframes + continuidad** (F): keyframe encadenado para coherencia.
- **v2-F5 · Orquestación completa + ensamblado** (H,I): cola, reintentos, reroll dirigido, ffmpeg → MP4 final.
- **v2-F6 · Pulido de prompting por proveedor + presets de coste** (economico/recomendado/premium).

**Primer paso accionable hoy (sin gastar):** v2-F1. Es local (yt-dlp+demucs+whisperx+librosa), no
necesita las keys de pago, y desbloquea la sincronía que diferencia el producto.

### v2-F1 — IMPLEMENTADO (2026-05-28)

Construido y testeado (16 tests verdes, sin binarios necesarios para CI):

- `backend/app/music_analysis.py` — `analyze_music()` (librosa: BPM/beats/duración/energía) + helpers puros `snap_times_to_beats()` y `sections_from_energy()`.
- `backend/app/audio_ingest.py` — orquestador `ingest_and_align()` (download → stems → align → music) con degradación elegante + helper puro `words_to_line_timings()` (palabras alineadas → tiempos por línea de letra, normaliza acentos/puntuación, interpola huecos).
- `backend/app/ingest_audio.py` — CLI.
- `backend/requirements-audio.txt` — extra de audio (yt-dlp, librosa, demucs, whisperx). NO va en CI.
- `backend/tests/test_audio_ingest.py` — tests de helpers puros.

Uso:
```
# 1) instalar el extra (una vez) + ffmpeg en PATH
pip install -r requirements-audio.txt

# 2) comprobar herramientas
python -m app.ingest_audio --check

# 3) URL + letra → tiempos por línea + BPM/beats
python -m app.ingest_audio --url "https://youtu.be/XXXX" --lyrics letra.txt -o timings.json
```
Sin las herramientas instaladas, el CLI corre igual y reporta qué pasos se degradaron.

**Siguiente:** v2-F2 (planner temporal real que consuma `line_timings` + beats en lugar de
la heurística de `timed_segments.py`).

---

## 9. Notas legales (importante)

- **YouTube/yt-dlp:** descargar viola los ToS de YouTube; legal solo si es **contenido propio**,
  Creative Commons o dominio público. Como es **tu canción**, encaja, pero déjalo documentado.
- **Spotify:** no se puede extraer audio (cifrado + prohibido). Solo metadata vía su API.
- **Letra:** mantener el gate de derechos del MVP (`lyrics_rights_confirmed`).
- En 2026 yt-dlp con YouTube a veces requiere PoToken/cookies frescas — prever fallback (subir archivo).

---

## 10. Fuentes (precios y herramientas, 2026)

- Pricing vídeo IA 2026 — buildmvpfast, evolink.ai, modelslab, fal.ai (Kling 3.0 $0.10/s, Veo 3.1 $0.75/$0.15, Wan 2.6 $0.05/s, Sora 2 deprecado sep-2026).
- yt-dlp / Spotify — audioutils, plisio, spotDL docs (Spotify no descargable).
- WhisperX forced alignment + Demucs — m-bain/whisperX, localaimaster, stable-ts.

*Documento de propuesta — 2026-05-28. Requiere aprobación para abrir milestone v2 y `/gsd-new-milestone`.*
