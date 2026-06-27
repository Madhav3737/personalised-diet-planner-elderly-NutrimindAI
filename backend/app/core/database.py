import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure DB URL
db_url = settings.DATABASE_URL
if settings.USE_SQLITE_FALLBACK and (not db_url or "localhost" in db_url or "postgres:postgres" in db_url):
    # If the user doesn't have pg config or it's a default host, we can fallback to SQLite
    # for easy plug-and-play local development
    db_url = settings.SQLITE_DATABASE_URL
    logger.info(f"Using SQLite database: {db_url}")

# Create engine
# SQLite needs different connect args
connect_args = {}
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}
    # For SQLite we need aiosqlite package, which we'll install/expect
    engine = create_async_engine(db_url, connect_args=connect_args)
else:
    engine = create_async_engine(db_url, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
