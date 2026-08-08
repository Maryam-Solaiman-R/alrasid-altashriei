import os
import secrets
import threading
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from source_monitor import scan_all


router = APIRouter(prefix="/api/v1", tags=["monitor"])

security = HTTPBearer(auto_error=False)


_monitor_state = {
    "status": "ready",
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}

_state_lock = threading.Lock()


def _run_scan():
    try:
        result = scan_all()

        with _state_lock:
            _monitor_state["status"] = "completed"
            _monitor_state["finished_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            _monitor_state["result"] = result
            _monitor_state["error"] = None

    except Exception as exc:
        with _state_lock:
            _monitor_state["status"] = "failed"
            _monitor_state["finished_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            _monitor_state["error"] = str(exc)[:1000]


@router.get("/monitor/status")
def status():
    with _state_lock:
        return dict(_monitor_state)


@router.post("/monitor/run")
def run_monitor(
    credentials: HTTPAuthorizationCredentials = Security(security),
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

    with _state_lock:
        if _monitor_state["status"] == "running":
            return {
                "status": "already_running",
                "message": "Monitor scan is already running"
            }

        _monitor_state["status"] = "running"
        _monitor_state["started_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        _monitor_state["finished_at"] = None
        _monitor_state["result"] = None
        _monitor_state["error"] = None

    worker = threading.Thread(
        target=_run_scan,
        daemon=True
    )
    worker.start()

    return {
        "status": "started",
        "message": "Monitor scan started in background"
    }
