# VideoZero

Monorepo MVP **Fase 1**: API FastAPI + SQLite + UI Next.js (Song Setup: proyecto, audio, letra, metadata, OPS-01, stub de encolado).

## Requisitos

- Node 20+
- Python 3.11+
- `ffmpeg` en PATH (para fases posteriores; la Fase 1 no lo invoca aún)

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:VIDEOZERO_DATA_DIR = "$(Resolve-Path ..)\backend\data"
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://127.0.0.1:8000/health`
- Datos: SQLite en `backend/data/videozero.db` (configurable con `VIDEOZERO_DATA_DIR` o `DATABASE_URL`).

## Frontend

```powershell
cd frontend
copy .env.local.example .env.local   # opcional; por defecto apunta a 127.0.0.1:8000
npm install
npm run dev
```

Abre `http://localhost:3000`: crea proyecto → Song Setup → guarda, sube audio, marca derechos, prueba el stub `POST /projects/{id}/analysis/enqueue`.

## GSD

Contexto de planificación en [`.planning/`](.planning/) y [docs/VIDEOZERO-MASTER.md](docs/VIDEOZERO-MASTER.md). Siguiente: **Fase 2** (jobs de análisis de audio + letra).
