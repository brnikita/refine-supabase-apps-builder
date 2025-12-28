import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import async_engine, sync_engine, Base
from app.api.routes import auth, apps, jobs, runtime

# Configure logging
logging.basicConfig(
   level=logging.INFO,
   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_db():
   """Initialize database schema."""
   with sync_engine.connect() as conn:
      # Create control_plane schema
      conn.execute(text("CREATE SCHEMA IF NOT EXISTS control_plane"))
      conn.commit()

   # Create all tables
   Base.metadata.create_all(bind=sync_engine)
   logger.info("Database initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
   # Startup
   logger.info("Starting up...")
   init_db()
   yield
   # Shutdown
   logger.info("Shutting down...")
   await async_engine.dispose()


app = FastAPI(
   title=settings.APP_NAME,
   description="Generate business web apps from natural language prompts",
   version="1.0.0",
   lifespan=lifespan
)

# CORS middleware
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # In production, specify actual origins
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(apps.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(runtime.router, prefix="/api")


@app.get("/api/health")
async def health_check():
   """Health check endpoint."""
   return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/")
async def root():
   """Root endpoint."""
   return {
      "message": "Blueprint Apps Builder API",
      "docs": "/docs",
      "health": "/api/health"
   }

