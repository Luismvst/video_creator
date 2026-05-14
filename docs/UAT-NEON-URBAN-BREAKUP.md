# UAT — Caso clásico: videoclip urbano nocturno / neón (melancolía post-relación)

**Versión:** 1.0 · 2026-05-13  
**Alcance:** MVP VideoZero (letra primero, sin render por API).  
**Objetivo:** Validar que un director/a pueda recorrer el flujo completo con un tema muy habitual en videoclips — ciudad de noche, neón, distancia emocional — y obtener **documentos + exports coherentes** sin audio obligatorio.

---

## Persona y premisa creativa

| Campo | Valor |
|--------|--------|
| Persona | Director/a independiente, primera vez en VideoZero |
| Tema | Pop/urbano melancólico; estética **neón + lluvia + coche/retrovisor** (referencias como *atributos*, no copiar obras) |
| Audio | **No** se sube pista (solo letra + duración objetivo opcional) |
| Idioma UI | Español (copy actual del MVP) |

---

## Datos de ejemplo (copiar en la app)

### Letra (4 líneas, ancla clara)

```text
Neón en el retrovisor
Fantasmas de domingo
Callamos como el asfalto
Cuando ya no queda historia
```

### Metadata sugerida

- **Título:** `Domingo de neón`  
- **Artista:** `UAT Ficticio`  
- **Mood:** `melancólico, urbano, nocturno`  
- **Duración objetivo (s):** `180`  
- **Pacing:** `slow_cinematic`  

### OPS

- Marcar **derechos de letra** confirmados (texto de prueba / propio).

### Estructura (STR-01)

| Sección | Tipo | Línea inicio | Línea fin |
|---------|------|--------------|-----------|
| Apertura | `verse` | 0 | 1 |
| Cierre | `chorus` | 2 | 3 |

Comprobar que **no** aparecen `structure_warnings` en rojo/ámbar antes del lock.

### Ideas (LYR-02)

- Pulsar **Generar ideas** en modo **heurística** (sin API key) *o* LLM si tienes clave.  
- Editar al menos una idea manualmente (texto propio).

### Dirección (JSON en pestaña *Dirección*)

**`creative_intake_json`** (ejemplo válido):

```json
{
  "reference_notes": "Ciudad húmeda, neón reflejado en charcos; silencios largos; nada de nombres de películas o videoclips reales.",
  "style_attributes": ["luz neón fría", "profundidad de campo corta", "cámara estable", "paleta azul-magenta"]
}
```

**`director_answers_json`**:

```json
{
  "visual_density": "media",
  "color_bible": "fría neón + sombras profundas",
  "protagonist_energy": "contenida",
  "ending_tone": "abierta / melancólica",
  "camera_language": "plano secuencia suave en intérieur coche"
}
```

**`creative_routes_json`**:

```json
{
  "routes": [
    {
      "id": "route-intimate",
      "title": "Ruta A — íntimo en el coche",
      "summary": "Todo el clip en espacio reducido; neón como único color de esperanza."
    },
    {
      "id": "route-walk",
      "title": "Ruta B — caminata bajo túneles",
      "summary": "Exterior nocturno; ritmo más fragmentado en montaje."
    }
  ]
}
```

**`selected_route_id`:** `route-intimate`  

Guardar cada bloque con **Guardar …** y luego **Cargar vista previa** (Visual Bible + Treatment).

### Plan (pestaña *Plan*)

**`shots_json`** (mínimo 2 planos):

```json
[
  {
    "slug": "retrovisor",
    "camera": "primer plano fijo retrovisor, reflejos",
    "action": "protagonista mira fijamente; neón parpadea en el cristal",
    "notes": "heredar paleta neón del intake"
  },
  {
    "slug": "asfalto",
    "camera": "plano detalle pies + charco",
    "action": "caminata lenta; reflejo distorsionado",
    "notes": "transición suave desde interior si se elige ruta A"
  }
]
```

**`generation_plan_json`** (al menos un paso):

```json
[
  {
    "title": "Referencias en moodboard interno",
    "detail": "Traducir notas a atributos (ya en intake); no pegar frames ajenos."
  },
  {
    "title": "Generación en herramienta externa",
    "detail": "Exportar prompts Runway o Kling y ejecutar allí; revisar continuidad con checklist."
  }
]
```

---

## Secuencia UAT (manual)

Marca **Pass / Fail** y notas.

| # | Paso | Criterio de éxito | Pass |
|---|------|-------------------|------|
| 1 | Crear proyecto desde home | Redirección o lista con nuevo proyecto | ☐ |
| 2 | Pestaña **Setup**: pegar letra + metadata + pacing + guardar | `GET` proyecto muestra datos; líneas en vista previa 0–3 | ☐ |
| 3 | Crear 2 secciones según tabla | Sin `structure_warnings` | ☐ |
| 4 | Generar ideas + editar una | Lista `insights` no vacía | ☐ |
| 5 | Pestaña **Dirección**: pegar JSON + ruta seleccionada + guardar | Sin error 400 de JSON inválido | ☐ |
| 6 | Vista previa documentos | Markdown contiene título/secciones o intake | ☐ |
| 7 | Pestaña **Plan**: `shots_json` + `generation_plan_json` + guardar | Persiste tras recargar página | ☐ |
| 8 | `POST …/analysis/enqueue` (botón gate) | `accepted_stub` + lista `recommendations` (puede avisar lock si aún no) | ☐ |
| 9 | **Creative Lock** | Lock OK sin warnings; snapshot presente | ☐ |
| 10 | Tras lock: intentar editar letra | Debe bloquearse (API 400 / UI read-only) | ☐ |
| 11 | Vista previa con lock | Sigue mostrando biblia/treatment (desde snapshot) | ☐ |
| 12 | Pestaña **Export**: abrir `bundle.md`, `shots.json`, `shots.csv`, `prompts.md?provider=runway` | Descargas 200; CSV con cabecera; JSON array coherente | ☐ |
| 13 | **Unlock** | Vuelve a permitir edición controlada | ☐ |

---

## Validación automática (CI / local)

El caso está reproducido en tests de API (misma base aislada que el resto de smoke tests):

```powershell
cd backend
python -m pytest tests/test_smoke.py::test_uat_neon_urban_breakup_journey -v
```

**Criterio:** el test debe pasar en verde antes de considerar este UAT “cerrado” en integración.

---

## Resultados esperados (comportamiento)

1. **Letra primero:** sin letra no se puede “encolar” el stub ni cerrar lock con sentido.  
2. **OPS:** sin confirmación de derechos de letra, lock y gate deben fallar donde corresponda.  
3. **Estructura:** warnings visibles si rangos incoherentes con la letra guardada.  
4. **Lock:** congela letra, secciones, ideas y JSON de plan; preview de documentos usa **snapshot**.  
5. **Export:** bundle y shots reflejan el estado (vivo o snapshot según lock).

---

## Registro de ejecución (rellenar en prueba real)

| Fecha | Ejecutor | Entorno (URL API / commit) | Resultado global | Incidencias |
|-------|----------|----------------------------|------------------|-------------|
| | | | Pass / Fail | |

---

## Fuera de este UAT (v2 / backlog)

- Render de vídeo por API.  
- Análisis DSP / BPM.  
- Editor visual de timeline (sustituir JSON crudo).  
- Jobs asíncronos reales sustituyendo el stub.
