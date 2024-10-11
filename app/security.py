from typing import Dict

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from app.database import get_db
from app.models import Key, User

API_KEY = APIKeyHeader(name="Api-Key")


def check_authentication_key(
    api_key: str = Depends(API_KEY), db: Session = Depends(get_db)
) -> Dict:
    """Takes the API-Key header and converts it into the matching user object
    from the database"""
    try:
        query = select(Key.user_id).where(Key.key == api_key)
        user_id = db.scalar(query)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DB not responding",
        )
    if user_id:
        return {"user_id": user_id}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


def create_first_user_for_login(db: Session):
    query = select(Key).where(Key.key == "test")
    result_key = db.scalars(query).one_or_none()
    if result_key is None:
        user = User(name="first user")
        db.add(user)
        db.commit()
        key = Key(user_id=user.id, key="test")
        db.add(key)
        db.commit()
