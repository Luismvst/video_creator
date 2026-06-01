# VideoZero — dry-run de render: Filomena

*Sin gasto · sin FAL_KEY · 7 segmentos · tope $25 · factor rerolls 1.4.*

## Coste estimado por proveedor (incluye factor de rerolls)

| Proveedor | Modelo fal | $/s | Vídeo (s) | Subtotal | Estimado* | ¿Cabe en tope? |
|---|---|---|---|---|---|---|
| kling | `fal-ai/kling-video/v2/standard/text-to-video` | 0.1 | 120.0 | $12.0 | **$16.8** | ✅ |
| veo3_fast | `fal-ai/veo3/fast` | 0.15 | 120.0 | $18.0 | **$25.2** | ❌ Estimado $25.20 supera el tope $25.00 (7 |
| veo3 | `fal-ai/veo3` | 0.75 | 120.0 | $90.0 | **$126.0** | ❌ Estimado $126.00 supera el tope $25.00 ( |
| runway | `fal-ai/runway-gen4/turbo` | 0.15 | 120.0 | $18.0 | **$25.2** | ❌ Estimado $25.20 supera el tope $25.00 (7 |
| wan | `fal-ai/wan/v2.6/text-to-video` | 0.05 | 120.0 | $6.0 | **$8.4** | ✅ |

*\* Estimado = subtotal × 1.4 (reserva para rerolls). El subtotal es el coste de una sola pasada.*

## Plan de render por segmento (Kling, dry-run — lo que se generaría)

### Clip 001 — 19.6s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_001.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 002 — 16.3s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_002.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 003 — 16.3s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_003.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 004 — 17.1s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_004.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 005 — 16.3s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_005.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 006 — 16.3s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_006.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

### Clip 007 — 18.1s · 16:9
- **Modelo:** `fal-ai/kling-video/v2/standard/text-to-video`
- **Salida:** `render_out\clip_007.mp4`
- **Prompt (preview):** # Prompt pack — Kling (capas)

> Biblia visual inyectada en cada plano. Referencias = atributos; nunca obras o artistas reales.
> Biblia: óptica lente 85mm, profundidad de campo muy corta · luz luz fría dominante con focos cálidos motivados

## Cómo lanzar el render real (cuando quieras gastar)

```powershell
cd backend
# 1) genera segments.json desde la sesión guiada (ya hecho para Filomena)
python _uat_filomena.py
# 2) dry-run del render (sin gastar): valida modelo, coste y gate
python -m app.render_cli --segments ../letras/filomena_segments.json --provider kling --max-budget 25
# 3) render REAL — primero 1 clip para validar calidad antes de la canción entera
$env:FAL_KEY = "<tu_clave_fal>"
python -m app.render_cli --segments ../letras/filomena_segments.json --provider kling --limit 1 --run
```

> El gate aborta automáticamente si el estimado supera `--max-budget`. Empieza con `--limit 1`.