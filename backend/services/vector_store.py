from config import settings
from langchain_core.documents import Document
from langchain_postgres import PGVector
import logging
from services.providers import get_embedding_provider
from typing import List, Tuple
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.connection_string = settings.database_url
        self.embeddings = get_embedding_provider()
        self.target_chunk_count = None
        
        try:
            self.vectorstore = PGVector(
                embeddings=self.embeddings,
                collection_name="financial_docs",
                connection=self.connection_string,
                use_jsonb=True,
            )
            logger.info(f"Connected to RDS Postgres Vector Store")
        except Exception as e:
            logger.error(f"Failed to init vector store: {e}")
            self.vectorstore = None

    def add_documents(self, documents: List[Document], batch_size: int = 32) -> None:
        if not self.vectorstore:
            logger.error("Vectorstore not initialized.")
            return

        if not documents:
            logger.warning("No documents provided to add to vector store.")
            return
            
        total = len(documents)
        logger.info(f"Adding {total} documents to Postgres.")
        
        for i in tqdm(range(0, total, batch_size), desc="[Embedding to RDS]", ncols=70):
            batch = documents[i: i + batch_size]
            self.vectorstore.add_documents(batch)
        
        logger.info("Documents successfully added to DB.")

    def similarity_search(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        if not self.vectorstore:
            return []

        if k is None:
            k = settings.retrieval_k
            
        try:
            t0 = time.time()
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            logger.info(f"Similarity search for '{query[:50]}...' returned {len(results)} chunks in {time.time()-t0:.3f}s")

            filtered = []
            for doc, distance in results:
                # Convert Distance -> Similarity (Asumsi Cosine)
                similarity_score = 1.0 - distance
                
                if similarity_score >= settings.similarity_threshold:
                    filtered.append((doc, similarity_score))
            
            if not filtered and results:
                logger.warning(f"All results below threshold {settings.similarity_threshold}. Returning top matches anyway.")
                return [(doc, 1.0 - dist) for doc, dist in results]
                
            return filtered
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    def get_document_count(self) -> int:
        return 0