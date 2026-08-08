import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_api import router as agent_router

app = FastAPI(
    title="الراصد التشريعي API",
    version="2.0",
    description="خدمة مبسطة للتحقق من الأنظمة واللوائح وتغييرات المواد من مصدرين رسميين.",
)

origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(agent_router)


@app.get("/")
def root():
    return {"name": "الراصد التشريعي", "version": "2.0", "status": "ready"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0"}
