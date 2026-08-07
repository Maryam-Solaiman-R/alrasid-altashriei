from fastapi import APIRouter
from live_connectors import public_connectors, connector_for_url
router=APIRouter(prefix="/api/v1",tags=["connectors"])
@router.get("/connectors")
def connectors(): return public_connectors()
@router.get("/connector")
def connector(url:str):
    c=connector_for_url(url)
    return c.__dict__ if c else {"status":"unregistered","url":url}
