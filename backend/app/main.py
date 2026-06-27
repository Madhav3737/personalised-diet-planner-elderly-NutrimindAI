import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.router import api_router
from app.rag.rag_pipeline import RAGPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Automatically create tables for easy local execution
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Initializing RAG database and ingestion...")
    try:
        rag = RAGPipeline(settings.DOCUMENTS_DIR, settings.VECTOR_DB_DIR)
        chunks_count = rag.ingest_documents()
        logger.info(f"Ingested {chunks_count} clinical chunks successfully on startup.")
    except Exception as e:
        logger.error(f"Failed to ingest RAG documents: {e}")
        
    yield
    # Shutdown actions (if any)
    logger.info("Shutting down NutriMind AI backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A Personalized RAG-Based Diet Planning Assistant for Elderly Healthcare",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access documentation at /docs",
        "status": "healthy"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
