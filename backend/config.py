import os
from typing import List, Optional
# Import SettingsConfigDict buat Pydantic V2
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # --- 1. General App Config ---
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    allowed_origins: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # --- 2. OpenAI / LLM Config ---
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "openai")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small") # Update ke model baru (optional)
    llm_model: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))

    # --- 3. Database Config ---
    database_url: str = os.getenv("DATABASE_URL", "") 
    vector_db_type: str = os.getenv("VECTOR_DB_TYPE", "postgres") 
    
    # AWS S3 Config
    s3_bucket_name: str = os.getenv("PDF_UPLOAD_BUCKET", "rag-pdf-storage-demo")
    
    # Credentials
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    # --- TAMBAH INI ---
    aws_session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN", None)
    
    aws_region: str = os.getenv("AWS_REGION", "ap-southeast-1")

    # --- 5. RAG Tuning ---
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    # --- FIX: Pydantic V2 Config ---
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()