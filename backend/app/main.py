import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db

logger = logging.getLogger("app")

app = FastAPI(
    title="Project Management & Task Tracking API",
    version="1.0.0",
    docs_url="/api/docs",  # under /api so the Nginx "/api" proxy rule also covers Swagger
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    # Full details go to the server log only. The client gets a safe, generic message.
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))  # fails (-> 500) if the database is unreachable
    return {"status": "ok"}
