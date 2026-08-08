import os
import socket
import time
import requests

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


@app.get("/api/v1/diagnostics/sources", tags=["diagnostics"])
def diagnose_sources():
    """تشخيص اتصال بيئة الاستضافة بالمصدرين الرسميين دون تغيير منطق الوكيل."""
    targets = [
        ("هيئة الخبراء بمجلس الوزراء", "laws.boe.gov.sa", "https://laws.boe.gov.sa/"),
        ("المركز الوطني للوثائق والمحفوظات", "ncar.gov.sa", "https://ncar.gov.sa/"),
    ]
    results = []
    for authority, host, url in targets:
        item = {"authority": authority, "host": host, "url": url}
        try:
            infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            ips = []
            for info in infos:
                ip = info[4][0]
                if ip not in ips:
                    ips.append(ip)
            item["dns"] = {"ok": True, "addresses": ips[:8]}
        except Exception as exc:
            item["dns"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            results.append(item)
            continue

        tcp_attempts = []
        for ip in item["dns"]["addresses"][:4]:
            family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            started = time.monotonic()
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                target = (ip, 443, 0, 0) if family == socket.AF_INET6 else (ip, 443)
                sock.connect(target)
                tcp_attempts.append({"ip": ip, "ok": True, "ms": round((time.monotonic()-started)*1000)})
            except Exception as exc:
                tcp_attempts.append({"ip": ip, "ok": False, "ms": round((time.monotonic()-started)*1000), "error": f"{type(exc).__name__}: {exc}"})
            finally:
                sock.close()
        item["tcp_443"] = tcp_attempts

        session = requests.Session()
        session.trust_env = False
        started = time.monotonic()
        try:
            r = session.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html,*/*"}, timeout=(4, 8), allow_redirects=True, stream=True)
            item["https_direct"] = {"ok": True, "status": r.status_code, "final_url": r.url, "ms": round((time.monotonic()-started)*1000)}
            r.close()
        except Exception as exc:
            item["https_direct"] = {"ok": False, "ms": round((time.monotonic()-started)*1000), "error": f"{type(exc).__name__}: {str(exc)[:240]}"}
        results.append(item)

    return {
        "status": "diagnostic_complete",
        "note": "هذا الفحص لا يغيّر بيانات الراصد ولا يجري بحثًا تشريعيًا.",
        "proxy_environment_present": any(os.getenv(k) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")),
        "sources": results,
    }
