from config import settings
import logging

logger = logging.getLogger(__name__)

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    # Pipeline tetap dari transformers standard
    from transformers import pipeline
except ImportError:
    HuggingFaceEmbeddings = None

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
except ImportError:
    OpenAIEmbeddings = None

def get_embedding_provider():
    if settings.embedding_provider.lower() == "openai":
        if not OpenAIEmbeddings:
            raise ImportError("Package 'langchain-openai' belum terinstall!")
        return OpenAIEmbeddings(
            api_key=settings.openai_api_key, 
            model=settings.embedding_model
        )
    elif settings.embedding_provider.lower() == "huggingface":
        if not HuggingFaceEmbeddings:
            raise ImportError("Package 'langchain-huggingface' belum terinstall!")
        return HuggingFaceEmbeddings(model_name=settings.embedding_model)
    else:
        raise ValueError(f"Unknown embedding_provider: {settings.embedding_provider}")

def get_llm_provider():    
    if settings.llm_provider.lower() == "openai":
        return ChatOpenAI(
            api_key=settings.openai_api_key, # Pake api_key, bukan openai_api_key (di versi baru)
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens
        )
    elif settings.llm_provider.lower() == "huggingface":
        # Pipeline QA standar
        return pipeline("question-answering", model=settings.llm_model)
    else:
        raise ValueError(f"Unknown llm_provider: {settings.llm_provider}")