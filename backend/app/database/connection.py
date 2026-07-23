"""
MongoDB Atlas async connection using Motor.
Implements a singleton pattern so the connection pool is created once
and reused across the app lifecycle.

When the configured Atlas endpoint is unreachable, the app falls back to a
lightweight in-memory collection implementation so local development and the
registration/auth flow can still be exercised.
"""
import copy
import logging
from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger("onedw.database")


def _matches_query(document: dict, query: dict) -> bool:
    """Return True when a document matches the provided query.
    Supports: simple equality, $exists, $regex (case-insensitive via $options).
    """
    import re as _re
    for key, expected in query.items():
        doc_val = document.get(key)
        if isinstance(expected, dict):
            # Handle operators
            if "$exists" in expected:
                has_key = key in document
                if expected["$exists"] and not has_key:
                    return False
                if not expected["$exists"] and has_key:
                    return False
            if "$regex" in expected:
                flags = _re.IGNORECASE if expected.get("$options", "") == "i" else 0
                if not _re.search(expected["$regex"], str(doc_val or ""), flags):
                    return False
        else:
            if doc_val != expected:
                return False
    return True



@dataclass
class MemoryInsertResult:
    """Minimal insert result object matching Motor's insert_one contract."""
    inserted_id: ObjectId


@dataclass
class MemoryUpdateResult:
    """Minimal update result object matching the service layer expectations."""
    matched_count: int = 0
    modified_count: int = 0


@dataclass
class MemoryDeleteResult:
    """Minimal delete result object matching the service layer expectations."""
    deleted_count: int = 0


class InMemoryCursor:
    """Lightweight async cursor implementation for the development fallback."""

    def __init__(self, documents: list[dict], query: dict):
        self._documents = documents
        self._query = query
        self._sort_field = None
        self._sort_direction = -1

    def sort(self, field: str, direction: int = -1):
        self._sort_field = field
        self._sort_direction = direction
        return self

    async def to_list(self, length: int | None = None) -> list[dict]:
        matches = [document for document in self._documents if _matches_query(document, self._query)]

        if self._sort_field is not None:
            matches.sort(
                key=lambda doc: doc.get(self._sort_field) or datetime.min,
                reverse=self._sort_direction == -1,
            )

        if length is not None:
            return matches[:length]
        return matches


class InMemoryCollection:
    """Small async collection wrapper used when MongoDB is unavailable."""

    def __init__(self):
        self._documents: list[dict] = []

    async def find_one(self, query: dict):
        for document in self._documents:
            if _matches_query(document, query):
                return copy.deepcopy(document)
        return None

    async def insert_one(self, document: dict) -> MemoryInsertResult:
        stored_document = copy.deepcopy(document)
        stored_document.setdefault("_id", ObjectId())
        self._documents.append(stored_document)
        return MemoryInsertResult(inserted_id=stored_document["_id"])

    def find(self, query: dict) -> InMemoryCursor:
        return InMemoryCursor(self._documents, query)

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> MemoryUpdateResult:
        updated = False
        for document in self._documents:
            if not _matches_query(document, query):
                continue

            set_payload = update.get("$set", {})
            for key, value in set_payload.items():
                document[key] = value

            # Handle $inc operator
            inc_payload = update.get("$inc", {})
            for key, delta in inc_payload.items():
                document[key] = document.get(key, 0) + delta

            updated = True
            break

        if not updated and upsert:
            new_doc = {**query}
            new_doc["_id"] = ObjectId()
            for key, value in update.get("$set", {}).items():
                new_doc[key] = value
            self._documents.append(new_doc)

        return MemoryUpdateResult(matched_count=1 if updated else 0, modified_count=1 if updated else 0)

    async def delete_one(self, query: dict) -> MemoryDeleteResult:
        for index, document in enumerate(self._documents):
            if _matches_query(document, query):
                del self._documents[index]
                return MemoryDeleteResult(deleted_count=1)
        return MemoryDeleteResult(deleted_count=0)

    async def count_documents(self, query: dict) -> int:
        if not query:
            return len(self._documents)
        return sum(1 for doc in self._documents if _matches_query(doc, query))


class InMemoryDatabase:
    """Development database facade — used when MongoDB Atlas is unreachable."""

    def __init__(self):
        self.users = InMemoryCollection()
        self.requests = InMemoryCollection()
        self.workers = InMemoryCollection()
        self.bookings = InMemoryCollection()
        self.ratings = InMemoryCollection()
        self.notifications = InMemoryCollection()
        self.test = InMemoryCollection()


class MongoDB:
    """Singleton wrapper around the Motor client and database handle."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | InMemoryDatabase | None = None
    using_in_memory: bool = False


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    """Initialize the MongoDB connection pool. Called on app startup."""
    logger.info("Connecting to MongoDB...")

    candidate_urls = [settings.mongodb_url]
    local_fallback = "mongodb://localhost:27017"
    if local_fallback not in candidate_urls:
        candidate_urls.append(local_fallback)

    last_error = None
    for mongo_url in candidate_urls:
        try:
            client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=8000,
                connectTimeoutMS=8000,
            )
            await client.admin.command("ping")
            mongodb.client = client
            mongodb.db = client[settings.mongodb_db_name]
            mongodb.using_in_memory = False
            logger.info("MongoDB connection established using %s", mongo_url)
            return
        except Exception as exc:
            last_error = exc
            logger.warning("MongoDB connection failed for %s: %s", mongo_url, exc)

    mongodb.client = None
    mongodb.db = InMemoryDatabase()
    mongodb.using_in_memory = True
    logger.warning(
        "MongoDB could not be initialized. Falling back to in-memory development storage. Last error: %s",
        last_error,
    )
    # Auto-seed demo workers so WorkerRecommendations always has results
    try:
        from app.database.in_memory_seed import seed_demo_workers
        await seed_demo_workers(mongodb.db)
        logger.info("In-memory DB seeded with %d demo workers.", 8)
    except Exception as seed_err:
        logger.warning("Demo seed failed: %s", seed_err)


async def close_mongo_connection() -> None:
    """Gracefully close the MongoDB connection. Called on app shutdown."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed.")

    mongodb.client = None
    mongodb.db = None
    mongodb.using_in_memory = False


async def check_db_health() -> bool:
    """Ping the database to verify connectivity — used in /health endpoint."""
    if mongodb.using_in_memory:
        return True

    if mongodb.client is None:
        return False

    try:
        await mongodb.client.admin.command("ping")
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False


def get_database() -> AsyncIOMotorDatabase | InMemoryDatabase:
    """Dependency-injectable accessor for the database instance."""
    if mongodb.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Check MongoDB settings and connectivity.",
        )
    return mongodb.db