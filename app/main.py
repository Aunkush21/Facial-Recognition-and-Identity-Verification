from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import attendance, audit, auth, enrollment, identities, recognition, users
from app.services.face_engine import get_face_engine
from app.services.liveness import get_liveness_checker
from app.web import pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_face_engine()
    get_liveness_checker()
    yield


app = FastAPI(title="Facial Recognition & Identity Verification", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(identities.router)
app.include_router(enrollment.router)
app.include_router(recognition.router)
app.include_router(attendance.router)
app.include_router(audit.router)
app.include_router(users.router)
app.include_router(pages.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
