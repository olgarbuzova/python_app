from typing import Dict

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery
from sqlalchemy import select
from starlette import status

from app.database import session
from app.models import Key

API_KEY = APIKeyHeader(name="Api-Key")


def check_authentication_key(api_key: str = Depends(API_KEY)) -> Dict:
    """Takes the API-Key header and converts it into the matching user object from the database"""
    try:
        query = select(Key.user_id).where(Key.key == api_key)
        user_id = session.scalar(query)
        if user_id:
            return {"user_id": user_id}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DB not responding",
        )
