from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.workflow import router as workflow_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Lab API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(workflow_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
