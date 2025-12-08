from config import settings
from langchain_core.documents import Document
import logging
from services.providers import get_llm_provider
from typing import List, Dict, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, vector_store: "VectorStoreService"):
        self.vector_store = vector_store
        self.llm = get_llm_provider()

    def generate_answer(self, question, chat_history=None):
        start_time = time.time()
        sources = []
        try:
            ret_docs_scores = self.vector_store.similarity_search(question)
            
            if not ret_docs_scores:
                logger.warning("No relevant document chunk found.")
                return {"answer": "Sorry, I could not find any relevant content.", "sources": [], "processing_time": 0.0}

            # Unpack tuples
            docs = [doc for doc, score in ret_docs_scores]
            
            for (doc, score) in ret_docs_scores:
                sources.append({
                    "content": doc.page_content,
                    "page": doc.metadata.get("page", "-"),
                    "score": float(score),
                    "metadata": doc.metadata,
                })
            
            context = self._generate_context(docs)
            answer = self._generate_llm_response(question, context, chat_history)
            
            proc_time = time.time() - start_time
            return {"answer": answer, "sources": sources, "processing_time": proc_time}
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return {"answer": f"System error: {e}", "sources": [], "processing_time": 0.0}

    def _generate_context(self, documents: List[Document]) -> str:
        context = "\n".join([doc.page_content for doc in documents])
        return context[:settings.max_tokens * 5]

    def _generate_llm_response(self, question: str, context: str, chat_history=None) -> str:
        if not context.strip():
            return "Sorry, no context found."
        
        try:
            if settings.llm_provider.lower() == "openai":
                prompt = f"""
                Answer based on context below. If calculation needed, show latex.
                
                Context:
                {context}

                Question:
                {question}
                """
                response_msg = self.llm.invoke(prompt)
                return response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
                
            elif settings.llm_provider.lower() == "huggingface":
                res = self.llm(question=question, context=context[:2000])
                return res.get("answer", "")
            else:
                return "[ERR: Provider not configured]"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"LLM error: {e}"