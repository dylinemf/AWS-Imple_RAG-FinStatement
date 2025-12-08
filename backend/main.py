from config import settings
from datetime import datetime
from fastapi import BackgroundTasks, FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import logging
from models.schemas import ChatRequest
import os
import boto3  # <--- WAJIB ADA
import shutil
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStoreService
from services.rag_pipeline import RAGPipeline
import time
import tempfile

# Configure logging
logging.basicConfig(
    level=settings.log_level, 
    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Financial App")

# Configure CORS (Buka "*" biar S3 Frontend bisa masuk)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
pdf_processor = PDFProcessor()
vector_store = VectorStoreService()
rag_pipeline = RAGPipeline(vector_store)

# S3 Client (Otomatis pake IAM Role App Runner, gaperlu key manual)
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    aws_session_token=settings.aws_session_token,
    region_name=settings.aws_region
)

def process_pdf_background(s3_key: str, local_tmp_path: str):
    """
    1. Download PDF dari S3 ke temp
    2. Extract text & Chunking
    3. Masukin ke Vector DB (RDS)
    4. Bersihin file temp
    """
    try:
        logger.info(f"Downloading {s3_key} from S3 to {local_tmp_path}...")
        s3_client.download_file(settings.s3_bucket_name, s3_key, local_tmp_path)
        
        docs = pdf_processor.process_pdf(local_tmp_path)
        
        # Set target count buat progress bar frontend
        try:
            vector_store.target_chunk_count = len(docs)
        except Exception:
            pass
            
        vector_store.add_documents(docs, batch_size=32)
        logger.info("Processing complete.")
        
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
    finally:
        # PENTING: Hapus file temp biar container gak penuh disknya
        if os.path.exists(local_tmp_path):
            os.remove(local_tmp_path)
            logger.info(f"Cleaned up temp file {local_tmp_path}")


@app.post("/api/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload ke S3 -> Trigger Process"""
    try:
        # Generate nama unik
        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"
        
        # 1. Upload Stream ke S3
        logger.info(f"Uploading {filename} to S3 bucket {settings.s3_bucket_name}...")
        s3_client.upload_fileobj(file.file, settings.s3_bucket_name, filename)
        
        # 2. Siapkan path temporary (FIX: Cross-platform Windows/Linux)
        local_tmp_path = os.path.join(tempfile.gettempdir(), filename)
        
        # 3. Trigger Background Task
        background_tasks.add_task(process_pdf_background, filename, local_tmp_path)
        
        return {"message": "PDF uploaded to S3 & processing started", "filename": filename}
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"answer": f"Error: {str(e)}", "sources": [], "processing_time": 0.0}

@app.get("/api/documents")
async def get_documents():
    """List documents dari S3 Bucket (Bukan folder lokal)"""
    try:
        response = s3_client.list_objects_v2(Bucket=settings.s3_bucket_name)
        documents = []
        
        # Cek kalau bucket kosong
        if 'Contents' in response:
            for obj in response['Contents']:
                # obj['LastModified'] is datetime
                documents.append({
                    "filename": obj['Key'],
                    "upload_date": obj['LastModified'],
                    "chunks_count": 0, # Susah ngitung chunk per file di vector DB, skip aja
                    "status": "processed"
                })
        return {"documents": documents}
    except Exception as e:
        logger.error(f"S3 List Error: {e}")
        return {"documents": []}

# ... (Endpoint /api/chat dan /api/chunks SAMA SAJA, tidak perlu ubah) ...
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Logic sama persis, karena dia manggil rag_pipeline.generate_answer
    # dan rag_pipeline manggil vector_store yang udah diperbaiki di atas.
    try:
        res = rag_pipeline.generate_answer(request.question)
        return res
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"answer": "Internal error", "sources": [], "processing_time": 0.0}

@app.get("/api/chunks")
async def get_chunks():
    # return kosong dulu aman biar frontend ga crash.
    total_target = getattr(vector_store, "target_chunk_count", 0)
    return {
        "chunks": [],
        "total_count": total_target, # Ini yg dipake progress bar
        "total_target_count": total_target
    }