
import os, secrets
from fastapi import APIRouter, Header, HTTPException
from source_monitor import scan_all
router=APIRouter(prefix="/api/v1",tags=["monitor"])

@router.get("/monitor/status")
def status():
    return {"status":"ready","message":"موصلات الرصد الحي جاهزة للتشغيل على الخادم المنشور."}

@router.post("/monitor/run")
def run_monitor(authorization: str | None = Header(default=None, alias="Authorization")):
    expected=os.getenv("MONITOR_TOKEN","")
 
        supplied=(authorization or "").removeprefix("Bearer ").strip()
        if not secrets.compare_digest(supplied,expected):
            raise HTTPException(status_code=401,detail="Unauthorized")
    return scan_all()
