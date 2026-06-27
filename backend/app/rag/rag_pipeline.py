import os
import glob
import logging
import pickle
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try importing FAISS, fallback to NumPy Cosine Similarity Vector Store if FAISS fails
try:
    import faiss
    FAISS_AVAILABLE = True
    logger.info("FAISS library imported successfully.")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS library not found. Falling back to NumPy-based Cosine Similarity Vector Store.")

# Try importing sentence_transformers, fallback to a dummy embedding generator if offline/missing
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("SentenceTransformers imported successfully.")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("SentenceTransformers not found. Fallback mock embedding generator will be used.")

class LocalEmbedder:
    """Wrapper around SentenceTransformer with fallback options."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Load sentence transformer model locally
                self.model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Error loading SentenceTransformer: {e}. Falling back to mock embeddings.")
                self.model = None

    def encode(self, texts: List[str]) -> np.ndarray:
        if self.model:
            return self.model.encode(texts, convert_to_numpy=True)
        else:
            # Generate deterministic mock embeddings for testing and fallback
            # We convert text characters to a numeric representation of length 384
            embeddings = []
            for text in texts:
                np.random.seed(sum(ord(c) for c in text[:100]) % 99999)
                vec = np.random.randn(384)
                vec /= np.linalg.norm(vec) or 1.0
                embeddings.append(vec)
            return np.array(embeddings, dtype=np.float32)


class SimpleVectorStore:
    """A clean NumPy-based Vector Store for fallback when FAISS is unavailable."""
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []

    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]):
        for i, vec in enumerate(vectors):
            self.vectors.append(vec / (np.linalg.norm(vec) or 1.0))
            self.metadata.append(metadata[i])

    def search(self, query_vector: np.ndarray, k: int = 3) -> List[Dict[str, Any]]:
        if not self.vectors:
            return []
        
        q_vec = query_vector / (np.linalg.norm(query_vector) or 1.0)
        matrix = np.array(self.vectors)
        # Cosine similarity is dot product when vectors are normalized
        similarities = np.dot(matrix, q_vec)
        
        # Sort indices by similarity descending
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_k_indices:
            results.append({
                "score": float(similarities[idx]),
                "metadata": self.metadata[idx]
            })
        return results

    def save(self, file_path: str):
        with open(file_path, "wb") as f:
            pickle.dump((self.vectors, self.metadata), f)

    def load(self, file_path: str):
        with open(file_path, "rb") as f:
            self.vectors, self.metadata = pickle.load(f)


class RAGPipeline:
    def __init__(self, documents_dir: str = "./documents", vector_db_dir: str = "./embeddings"):
        self.documents_dir = documents_dir
        self.vector_db_dir = vector_db_dir
        self.embedder = LocalEmbedder()
        self.index = None
        self.metadata_store: List[Dict[str, Any]] = []
        
        # Create directories if they don't exist
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.vector_db_dir, exist_ok=True)
        
        self.dimension = 384 # Dimension for all-MiniLM-L6-v2

        # Initialize vector store representation
        if FAISS_AVAILABLE:
            self.faiss_index = faiss.IndexFlatIP(self.dimension) # Inner product similarity (equivalent to cosine when normalized)
        else:
            self.numpy_store = SimpleVectorStore(self.dimension)

    def chunk_text(self, text: str, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
        """Splits document text into overlapping chunks recursively based on paragraph breaks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle paragraphs larger than chunk_size by splitting on sentences
                if len(para) > chunk_size:
                    sentences = para.replace(". ", ".\n").split("\n")
                    sub_chunk = ""
                    for sent in sentences:
                        if len(sub_chunk) + len(sent) <= chunk_size:
                            sub_chunk += sent + " "
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk.strip())
                            sub_chunk = sent + " "
                    current_chunk = sub_chunk
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def ingest_documents(self) -> int:
        """Loads files from documents directory, chunks them, generates embeddings, and saves to index."""
        logger.info("Starting ingestion of documents...")
        all_chunks = []
        all_metadata = []
        
        # Load .txt and .md files
        search_pattern = os.path.join(self.documents_dir, "**", "*.*")
        files = []
        for ext in ["*.txt", "*.md", "*.json"]:
            files.extend(glob.glob(os.path.join(self.documents_dir, "**", ext), recursive=True))
            files.extend(glob.glob(os.path.join(self.documents_dir, ext)))
            
        # Deduplicate file paths
        files = list(set(files))
        
        if not files:
            logger.warning(f"No text, markdown, or JSON files found in {self.documents_dir}")
            return 0

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                filename = os.path.basename(file_path)
                chunks = self.chunk_text(content)
                logger.info(f"Ingested {filename}: generated {len(chunks)} chunks.")
                
                for idx, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append({
                        "source": filename,
                        "chunk_id": idx,
                        "text": chunk
                    })
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")

        if not all_chunks:
            return 0

        # Create embeddings
        embeddings = self.embedder.encode(all_chunks)
        
        # Normalize for inner product (cosine) similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / np.where(norms == 0, 1.0, norms)
        
        # Store in FAISS or NumPy
        if FAISS_AVAILABLE:
            self.faiss_index = faiss.IndexFlatIP(self.dimension)
            self.faiss_index.add(embeddings_normalized.astype(np.float32))
            self.metadata_store = all_metadata
            # Save FAISS
            faiss.write_index(self.faiss_index, os.path.join(self.vector_db_dir, "faiss.index"))
            with open(os.path.join(self.vector_db_dir, "metadata.pkl"), "wb") as f:
                pickle.dump(self.metadata_store, f)
        else:
            self.numpy_store = SimpleVectorStore(self.dimension)
            self.numpy_store.add(embeddings_normalized, all_metadata)
            self.numpy_store.save(os.path.join(self.vector_db_dir, "numpy_store.pkl"))

        logger.info(f"Ingestion complete. Total ingested chunks: {len(all_chunks)}")
        return len(all_chunks)

    def load_index(self) -> bool:
        """Loads index from disk."""
        if FAISS_AVAILABLE:
            index_path = os.path.join(self.vector_db_dir, "faiss.index")
            meta_path = os.path.join(self.vector_db_dir, "metadata.pkl")
            if os.path.exists(index_path) and os.path.exists(meta_path):
                try:
                    self.faiss_index = faiss.read_index(index_path)
                    with open(meta_path, "rb") as f:
                        self.metadata_store = pickle.load(f)
                    logger.info("Successfully loaded FAISS index and metadata.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to load FAISS index: {e}")
                    return False
        else:
            numpy_path = os.path.join(self.vector_db_dir, "numpy_store.pkl")
            if os.path.exists(numpy_path):
                try:
                    self.numpy_store.load(numpy_path)
                    logger.info("Successfully loaded NumPy-based Vector Store.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to load NumPy store: {e}")
                    return False
        return False

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Given a search query, retrieves top k matching paragraphs/chunks."""
        # Ensure index is loaded
        if FAISS_AVAILABLE:
            if self.faiss_index.ntotal == 0:
                if not self.load_index():
                    # Attempt ingestion if index empty
                    self.ingest_documents()
            
            if self.faiss_index.ntotal == 0:
                return []
                
            query_vector = self.embedder.encode([query])
            norm = np.linalg.norm(query_vector)
            query_vector_normalized = query_vector / (norm if norm > 0 else 1.0)
            
            scores, indices = self.faiss_index.search(query_vector_normalized.astype(np.float32), k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.metadata_store):
                    continue
                results.append({
                    "score": float(scores[0][i]),
                    "text": self.metadata_store[idx]["text"],
                    "source": self.metadata_store[idx]["source"]
                })
            return results
        else:
            if not self.numpy_store.vectors:
                if not self.load_index():
                    self.ingest_documents()
            
            if not self.numpy_store.vectors:
                return []
                
            query_vector = self.embedder.encode([query])[0]
            search_results = self.numpy_store.search(query_vector, k)
            
            results = []
            for res in search_results:
                results.append({
                    "score": res["score"],
                    "text": res["metadata"]["text"],
                    "source": res["metadata"]["source"]
                })
            return results
