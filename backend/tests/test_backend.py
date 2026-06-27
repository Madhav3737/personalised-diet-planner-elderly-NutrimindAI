import pytest
import numpy as np
from app.core.security import get_password_hash, verify_password
from app.rag.rag_pipeline import SimpleVectorStore, RAGPipeline
from app.services.profile_service import ProfileService
from app.services.recommendation_service import RecommendationService
from app.schemas.schemas import ProfileCreate, MedicalHistoryCreate

def test_password_hashing():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_bmi_calculation_logic():
    # Height: 165cm, Weight: 65kg
    # BMI = 65 / (1.65 * 1.65) = 23.875
    height_m = 165 / 100.0
    bmi = round(65 / (height_m * height_m), 1)
    assert bmi == 23.9

def test_numpy_vector_store():
    store = SimpleVectorStore(dimension=4)
    v1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32)
    
    store.add(np.array([v1, v2, v3]), [
        {"text": "Chunk 1"},
        {"text": "Chunk 2"},
        {"text": "Chunk 3"}
    ])
    
    # Query close to v1
    query = np.array([1.0, 0.05, 0.0, 0.0], dtype=np.float32)
    results = store.search(query, k=2)
    
    assert len(results) == 2
    assert results[0]["metadata"]["text"] == "Chunk 1"
    assert results[1]["metadata"]["text"] == "Chunk 3"

def test_text_chunking():
    pipeline = RAGPipeline()
    text = "This is a paragraph.\n\nThis is another paragraph that we want to chunk."
    chunks = pipeline.chunk_text(text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) == 2
    assert chunks[0] == "This is a paragraph."
    assert "another paragraph" in chunks[1]
