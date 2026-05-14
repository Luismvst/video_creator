# VideoZero

Monorepo **MVP v1**: director creativo **letra primero**. **FastAPI** + **SQLite** + **Next.js** (App Router, Tailwind). Audio opcional; OPS letra + OPS audio condicional; **Creative Lock** con snapshot; preview y exports Markdown/JSON/CSV.

> Si actualizas el modelo y falla SQLite por columnas nuevas, en **desarrollo** borra `backend/data/videozero.db` y reinicia la API para recrear tablas. Para producción, planifica migraciones (ver backlog en `.planning/PROJECT.md`).

## Requisitos

- Node 20+
- Python 3.11+ (CI usa 3.12)
- `ffmpeg` en PATH (reservado para *Audio Pro* / futuras fases; el MVP no lo invoca)

## CI

En GitHub: workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — `pytest` en `backend/`, `npm run build` en `frontend/`.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:VIDEOZERO_DATA_DIR = "$(Resolve-Path ..)\backend\data"
uvicorn app.main:app --reload --port 8000
```

### Health

`GET http://127.0.0.1:8000/health`

### Proyecto y canción

| Método | Ruta | Notas |
|--------|------|--------|
| `POST` | `/projects` | Crear proyecto (incluye `song` vacía) |
| `GET` | `/projects` | Listado |
| `GET` | `/projects/{id}` | Detalle + `song` (secciones, ideas, warnings, campos JSON, `creative_locked`) |
| `PATCH` | `/projects/{id}/song` | Metadata, letra, pacing, OPS, JSON de plan/dirección (bloqueado parcialmente con Creative Lock) |
| `POST` | `/projects/{id}/song/audio` | Subida multipart (bloqueado si hay Creative Lock) |

### Letra y estructura (STR / LYR)

- `GET /projects/{id}/song/lines`
- `POST|PATCH|DELETE /projects/{id}/song/sections`, `PUT …/sections/reorder` (body `{ "section_ids": [...] }`)
- `POST /projects/{id}/song/insights/generate`, CRUD + `PUT …/insights/reorder` — heurística y/o OpenAI opcional (`VIDEOZERO_OPENAI_API_KEY` o `OPENAI_API_KEY`)

### Dirección y documentos

- `POST /projects/{id}/creative/lock` — requiere letra + derechos + sin `structure_warnings`
- `POST /projects/{id}/creative/unlock`
- `GET /projects/{id}/documents/preview` — JSON: `visual_bible_markdown`, `treatment_markdown` (usa snapshot si hay lock)

### Export (EXP)

| `GET` | Descripción |
|-------|-------------|
| `/projects/{id}/export/bundle.md` | Biblia + treatment + plan de generación + prompts genéricos |
| `/projects/{id}/export/prompts.md?provider=generic\|runway\|kling` | Solo prompts |
| `/projects/{id}/export/shots.json` | Array desde `shots_json` (snapshot si lock) |
| `/projects/{id}/export/shots.csv` | Columnas `index,slug,camera,action,notes` |

### Pipeline (stub)

`POST /projects/{id}/analysis/enqueue` — valida letra + OPS (y audio si aplica). **No encola jobs.** Respuesta: `status`, `message`, `recommendations[]` (siguientes pasos sugeridos).

### Config opcional LLM

`VIDEOZERO_OPENAI_API_KEY` o `OPENAI_API_KEY`; modelo por defecto `gpt-4o-mini` (`VIDEOZERO_OPENAI_MODEL`).

### Datos

SQLite en `backend/data/videozero.db` (`VIDEOZERO_DATA_DIR` o `DATABASE_URL`).

### Tests

```powershell
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Frontend

```powershell
cd frontend
copy .env.local.example .env.local   # opcional; API por defecto 127.0.0.1:8000
npm install
npm run dev
```

Abre `http://localhost:3000`: crea proyecto → pestañas **Setup** (letra, pacing, secciones, ideas), **Dirección** (JSON + lock + preview), **Plan** (timings + planificación JSON), **Export** (enlaces directos a la API).

## GSD

[`.planning/`](.planning/) — [ROADMAP.md](.planning/ROADMAP.md), [PROJECT.md](.planning/PROJECT.md), [STATE.md](.planning/STATE.md). Especificación: [docs/VIDEOZERO-MASTER.md](docs/VIDEOZERO-MASTER.md). **UAT ejemplo (caso clásico neón urbano):** [docs/UAT-NEON-URBAN-BREAKUP.md](docs/UAT-NEON-URBAN-BREAKUP.md).
