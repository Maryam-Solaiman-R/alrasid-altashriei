import os
import secrets

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from source_monitor import scan_all


router = APIRouter(prefix="/api/v1", tags=["monitor"])

security = HTTPBearer(auto_error=False)


@router.get("/monitor/status")
def status():
    return {
        "status": "ready",
        "message": "مرصد المصادر جاهز للتشغيل"
    }


@router.post("/monitor/run")
def run_monitor(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    expected = os.getenv("MONITOR_TOKEN", "").strip()

    if not expected:
        raise HTTPException(
            status_code=500,
            detail="MONITOR_TOKEN is not configured"
        )

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not secrets.compare_digest(
            credentials.credentials.strip(),
            expected
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return scan_all()
