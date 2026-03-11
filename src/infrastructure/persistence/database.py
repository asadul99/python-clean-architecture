"""
Database engine & session factory — equivalent to DbContext configuration in C#.
Uses SQLAlchemy 2.0 async engine (like EF Core with async).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from infrastructure.config import settings

# Engine = connection pool (like EF Core's DbContextOptions)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

# Session factory = scoped DbContext factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

