from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import Base, engine, session
from app.routes import create_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        content={
            "result": False,
            "error_type": "HTTPException",
            "error_message": exc.detail,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc) -> JSONResponse:
    return JSONResponse(
        content={
            "result": False,
            "error_type": "RequestValidationError",
            "error_message": exc.detail,
        },
        status_code=exc.status_code,
    )


create_routes(app)
