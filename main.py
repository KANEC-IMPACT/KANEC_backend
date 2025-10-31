from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from api.utils.settings import settings
from api.v1.routes import api_version_one

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    root_path="/kanec"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
app.mount("/static/projects/", StaticFiles(directory="static"), name="static")

app.include_router(api_version_one)

@app.get("/")
def healthcheck():
    return {"status": "ok"}