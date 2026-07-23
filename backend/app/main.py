"""
OneDW Backend — FastAPI application entrypoint.
Wires together config, database lifecycle, middleware, routers, and error handling.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers import auth_router, request_router, worker_router, booking_router, ai_router, rating_router

from app.config import settings
from app.database.connection import (
    connect_to_mongo,
    close_mongo_connection,
    check_db_health,
    get_database,
)
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("onedw.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown: connect DB on start, close it on shutdown."""
    await connect_to_mongo()
    logger.info(f"OneDW backend started in '{settings.app_env}' mode.")
    yield
    await close_mongo_connection()
    logger.info("OneDW backend shut down cleanly.")


app = FastAPI(
    title="OneDW API",
    description="AI-powered Hyperlocal Home Services Platform — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[0-9]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Middleware
# -------------------------
app.add_middleware(LoggingMiddleware)

# -------------------------
# Exception Handlers
# -------------------------
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)

# -------------------------
# Routers
# -------------------------
app.include_router(auth_router.router)
app.include_router(request_router.router)
app.include_router(worker_router.router)
app.include_router(booking_router.router)
app.include_router(ai_router.router)
app.include_router(rating_router.router)

# -------------------------
# Root
# -------------------------
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "OneDW API is running.",
        "docs": "/docs",
    }


# -------------------------
# Health Check
# -------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_health()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": db_ok,
    }


# -------------------------
# MongoDB Test
# -------------------------
@app.get("/mongo-test", tags=["Database"])
async def mongo_test():
    db = get_database()

    result = await db.test.insert_one(
        {
            "message": "MongoDB Connected Successfully"
        }
    )

    return {
        "status": "success",
        "inserted_id": str(result.inserted_id),
    }