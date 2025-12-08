from config import settings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
import os
import pdfplumber
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ".", " "]
        )
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF and return page-wise content"""
        pages_content = []
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if not text.strip():
                        logger.warning(f"Page {i+1} in {file_path} is empty or unreadable.")
                    pages_content.append({"page": i+1, "content": text})
            logger.info(f"Extracted {len(pages_content)} pages from PDF '{file_path}'")
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            raise RuntimeError(f"Fail top open or process the PDF: {e}")
        return pages_content

    def clean_page_content(self, text: str) -> str:
        """Remove unusual unicode, normalize spaces (optional for messy scans)"""
        return ' '.join(text.replace("\xa0", " ").split())

    def split_into_chunks(self, pages_content: List[Dict[str, Any]]) -> List[Document]:
        """Split page content into chunks, return Langchain Document objects with page metadata"""
        docs = []
        for page in pages_content:
            clean_content = self.clean_page_content(page["content"])
            chunks = self.splitter.split_text(clean_content)
            for c in chunks:
                docs.append(
                    Document(
                        page_content=c,
                        metadata={"page": page["page"]}
                    )
                )
        logger.info(f"Total {len(docs)} chunks generated from {len(pages_content)} PDF pages.")
        return docs

    def process_pdf(self, file_path: str) -> List[Document]:
        """Process PDF file and return list of Document objects"""
        pages = self.extract_text_from_pdf(file_path)
        if not any(p["content"].strip() for p in pages):
            logger.error("No extractable text found in PDF!")
            raise ValueError("No extractable text found in PDF!")
        return self.split_into_chunks(pages)