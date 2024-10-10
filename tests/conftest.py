import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.database import Base, get_db
from app.main import app
from app.models import Key, User

load_dotenv(dotenv_path=".env.testing", override=True)

PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_HOST = os.environ.get("PG_HOST")
PG_DATABASE = os.environ.get("PG_DATABASE")
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}/{PG_DATABASE}"
)
TEST_USER = {"username": "test_user", "api_key": "test_key"}
FAKE_USER = {"username": "fake_user", "api_key": "fake_key"}

test_engine = create_engine(TEST_DATABASE_URL)

if database_exists(TEST_DATABASE_URL):
    drop_database(TEST_DATABASE_URL)
create_database(TEST_DATABASE_URL)

Base.metadata.create_all(test_engine)
TestingSession = sessionmaker(
    autoflush=False, bind=test_engine, expire_on_commit=False
)


def override_get_db():
    try:
        db = TestingSession()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def prepare():
    db_session = TestingSession()
    test_user = User(name=TEST_USER["username"])
    fake_user = User(name=FAKE_USER["username"])
    db_session.add(test_user)
    db_session.add(fake_user)
    db_session.commit()

    test_key = Key(user_id=test_user.id, key=TEST_USER["api_key"])
    fake_key = Key(user_id=fake_user.id, key=FAKE_USER["api_key"])
    db_session.add(test_key)
    db_session.add(fake_key)
    db_session.commit()
    db_session.close()

    yield TestingSession
    test_engine.dispose()
    drop_database(TEST_DATABASE_URL)


client = TestClient(app)
