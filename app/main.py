from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.database import Base, engine, session
from app.routes import create_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

create_routes(app)
