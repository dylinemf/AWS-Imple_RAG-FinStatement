from config import settings
from datetime import datetime
from fastapi import BackgroundTasks, FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import logging
from models.schemas import ChatRequest
import os
import boto3
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

# Configure CORS to allow the frontend to access the API.
# The wildcard "*" is used for simplicity in this development environment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize application services
pdf_processor = PDFProcessor()
vector_store = VectorStoreService()
rag_pipeline = RAGPipeline(vector_store)

# S3 Client setup.
# In a production environment like AWS App Runner, this would automatically use
# the assigned IAM role. For local development, it uses credentials from the .env file.
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    aws_session_token=settings.aws_session_token,
    region_name=settings.aws_region
)

def process_pdf_background(s3_key: str, local_tmp_path: str):
    """
    Asynchronously processes a PDF file after it has been uploaded to S3.

    This background task is responsible for the entire ingestion pipeline:
    1. Downloads the PDF from S3 to a local temporary path.
    2. Extracts text and splits it into manageable chunks.
    3. Embeds the chunks and stores them in the PostgreSQL vector database.
    4. Cleans up the temporary file to free up disk space.

    Args:
        s3_key: The object key for the PDF file in the S3 bucket.
        local_tmp_path: The local temporary path where the file will be downloaded.
    """
    try:
        logger.info(f"Downloading {s3_key} from S3 to {local_tmp_path}...")
        s3_client.download_file(settings.s3_bucket_name, s3_key, local_tmp_path)

        docs = pdf_processor.process_pdf(local_tmp_path)

        # Set the target chunk count to provide progress feedback to the frontend.
        # This is a simple mechanism to let the UI know the total number of chunks
        # to expect during the embedding process.
        try:
            vector_store.target_chunk_count = len(docs)
        except Exception:
            pass  # Fails silently if the attribute doesn't exist or isn't settable.

        vector_store.add_documents(docs, batch_size=32)
        logger.info("Processing complete.")

    except Exception as e:
        logger.error(f"Background processing failed: {e}")
    finally:
        # CRITICAL: Clean up the temporary file to prevent the container's
        # disk from filling up, especially in a serverless environment.
        if os.path.exists(local_tmp_path):
            os.remove(local_tmp_path)
            logger.info(f"Cleaned up temporary file: {local_tmp_path}")


@app.post("/api/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Handles PDF file uploads.

    This endpoint streams the uploaded file directly to an S3 bucket and then
    triggers a background task to process it for the RAG pipeline. This
    ensures the endpoint returns quickly without waiting for the heavy
    processing (parsing, chunking, embedding) to complete.

    Args:
        background_tasks: FastAPI's mechanism for running background operations.
        file: The uploaded PDF file.

    Returns:
        A confirmation message and the unique filename assigned to the S3 object.
    """
    try:
        # Generate a unique filename using a timestamp to avoid collisions.
        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"

        # 1. Stream the file directly to the S3 bucket.
        logger.info(f"Uploading {filename} to S3 bucket {settings.s3_bucket_name}...")
        s3_client.upload_fileobj(file.file, settings.s3_bucket_name, filename)

        # 2. Prepare a cross-platform compatible temporary path for the background task.
        local_tmp_path = os.path.join(tempfile.gettempdir(), filename)

        # 3. Add the processing task to the background queue.
        background_tasks.add_task(process_pdf_background, filename, local_tmp_path)

        return {"message": "PDF uploaded to S3 & processing started", "filename": filename}

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"answer": f"Error: {str(e)}", "sources": [], "processing_time": 0.0}

@app.get("/api/documents")
async def get_documents():
    """
    Retrieves a list of processed documents from the S3 bucket.

    This provides the frontend with a list of available knowledge bases.
    It does not query the local filesystem.

    Returns:
        A list of document objects, each containing metadata like
        filename and upload date.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=settings.s3_bucket_name)
        documents = []

        # Check if the bucket has any contents.
        if 'Contents' in response:
            for obj in response['Contents']:
                # obj['LastModified'] is a datetime object.
                documents.append({
                    "filename": obj['Key'],
                    "upload_date": obj['LastModified'],
                    # NOTE: Calculating chunk count per file from the vector DB is complex
                    # with the current schema, so it's omitted for now.
                    "chunks_count": 0,
                    "status": "processed"
                })
        return {"documents": documents}
    except Exception as e:
        logger.error(f"S3 List Error: {e}")
        return {"documents": []}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Handles a user's question and generates a RAG-based answer.

    This endpoint delegates the entire process to the RAGPipeline service,
    which handles query embedding, context retrieval, and answer generation.

    Args:
        request: A ChatRequest object containing the user's question.

    Returns:
        An answer object containing the generated text and source citations.
    """
    try:
        res = rag_pipeline.generate_answer(request.question)
        return res
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"answer": "Internal error", "sources": [], "processing_time": 0.0}

@app.get("/api/chunks")
async def get_chunks():
    """
    Provides progress information for the document ingestion process.

    While this endpoint is named `get_chunks`, its primary role here is to
    return the total number of chunks expected during processing, which the
    frontend uses to display a progress bar. A full implementation might
    stream actual chunk data.

    Returns:
        A dictionary containing chunk information, primarily the target count.
    """
    # This is a simplified implementation for the progress bar.
    # It returns an empty list of chunks but provides the total count
    # that the vector store is expected to process.
    total_target = getattr(vector_store, "target_chunk_count", 0)
    return {
        "chunks": [],
        "total_count": total_target,
        "total_target_count": total_target
    }