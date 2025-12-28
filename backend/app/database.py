from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Async engine for FastAPI
async_engine = create_async_engine(
   settings.DATABASE_URL,
   echo=settings.DEBUG,
   future=True,
)

AsyncSessionLocal = async_sessionmaker(
   async_engine,
   class_=AsyncSession,
   expire_on_commit=False,
)

# Sync engine for migrations and schema creation
sync_engine = create_engine(
   settings.DATABASE_URL_SYNC,
   echo=settings.DEBUG,
)

SyncSessionLocal = sessionmaker(
   bind=sync_engine,
   autocommit=False,
   autoflush=False,
)


class Base(DeclarativeBase):
   pass


async def get_db() -> AsyncSession:
   async with AsyncSessionLocal() as session:
      try:
         yield session
      finally:
         await session.close()


def get_sync_db():
   db = SyncSessionLocal()
   try:
      yield db
   finally:
      db.close()

