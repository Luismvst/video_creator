from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers.creative_direction import router as creative_direction_router
from .routers.documents import router as documents_router
from .routers.export_bundle import router as export_bundle_router
from .routers.health import router as health_router
from .routers.lyrics_insights import router as lyrics_insights_router
from .routers.lyrics_structure import router as lyrics_structure_router
from .routers.onboarding import router as onboarding_router
from .routers.projects import router as projects_router

app = FastAPI(title="VideoZero API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(onboarding_router)
app.include_router(lyrics_structure_router)
app.include_router(lyrics_insights_router)
app.include_router(creative_direction_router)
app.include_router(documents_router)
app.include_router(export_bundle_router)


@app.on_event("startup")
def on_startup():
    init_db()
