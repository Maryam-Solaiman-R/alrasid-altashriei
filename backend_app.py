
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(title="الراصد التشريعي API",version="1.6")

origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS","").split(",") if x.strip()]
if not origins:
    origins=["http://localhost:8000","http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST"],
    allow_headers=["Content-Type","Authorization"],
)

@app.get("/")
def root():
    return {"name":"الراصد التشريعي","version":"1.6","status":"ready"}

@app.get("/health")
def health():
    return {"status":"ok","version":"1.6"}

# Routers are isolated so one optional component does not prevent startup.
for module_name in ("article_api","agent_api","connector_api","monitor_api","query_api"):
    try:
        module=__import__(module_name)
        app.include_router(module.router)
    except Exception as exc:
        print(f"Router {module_name} not loaded: {exc}")
