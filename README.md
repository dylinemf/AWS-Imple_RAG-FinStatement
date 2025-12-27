# RAG-Financial-Statement — Additional Notes

- **Project Structure**
```
RAG-Financial-Statement/
├── backend/
│ ├── main.py                 # FastAPI application
│ ├── models/                 # Data models
│ │ └── schemas.py            # Pydantic schemas
│ ├── services/               # RAG service logic
│ │ ├── pdf_processor.py      # PDF processing and chunking
│ │ ├── providers.py          # Embeddings and LLM management (HF & OpenAI)
│ │ ├── vector_store.py       # Vector database integration
│ │ └── rag_pipeline.py       # RAG pipeline
│ ├── requirements.txt        # Python dependencies
│ └── config.py               # Configuration file
├── frontend/
│ ├── pages/                  # Next.js pages
│ │ ├── index.tsx             # Main page
│ │ └── _app.tsx              # App component
│ ├── components/             # React components
│ │ ├── ChatInterface.tsx
│ │ └── FileUpload.tsx
│ ├── hooks/                        # Hooks
│ │ └── useKnowledgeBase.ts         # Trigger based on batch process
│ ├── styles/                       # CSS files
│ │ └── globals.css                 # Global styles
│ │ └── ChatInterface.module.css    # Module style
│ │ └── FileUpload.module.css       # Module style
│ ├── public/                       # folder for public usecases like icon
│ │ └── favicon.png
│ ├── package.json                  # Node.js dependencies
│ ├── tsconfig.json                 # TypeScript configuration
│ ├── next.config.js                # Next.js configuration
│ ├── next-env.d.ts                 # Next.js type definitions
│ └── .eslintrc.json                # ESLint configuration
├── data/
│ └── sample.pdf
└── README.md
```

## 🚩 What's Different in This Repo

- **Modular Provider Management (`providers.py`):**
  - Added a `providers.py` file to make embedding and LLM provider (HuggingFace or OpenAI) selection more modular and extensible. You just configure via env variables.

- **Not Using `_retrieve_documents`:**
  - The function `_retrieve_documents` from the original repo is not used here.
  - All retrieval is handled in `vector_store.py` via `similarity_search`, called directly from the RAG pipeline (`generate_answer`). So there's no dependency on that function.

- **Frontend Response Formatting:**
  - Added `react-markdown`, `remark-math`, and `katex` to render model responses with markdown and math formatting, making answers much cleaner and easier to read.

- **Embeddings & LLM Provider Choice:**
  - You can select either HuggingFace or OpenAI for both embeddings and LLM, simply by changing values in the `.env` file (see `.env`). To use OpenAI, supply your own `OPENAI_API_KEY`.
  
  Sample `.env`:
  ```
  OPENAI_API_KEY= """                         # Fill with our own OpenAI API-Key
  VECTOR_DB_PATH="./vector_store"             # A folder to store vectorstore, already a default
  VECTOR_DB_TYPE="chromadb"                   # 'chromadb' also already a default
  PDF_UPLOAD_PATH="../data"                   # A folder to store the uploaded PDF
  LLM_TEMPERATURE=0.1
  MAX_TOKENS=1000
  CHUNK_SIZE=1000
  CHUNK_OVERLAP=200
  RETRIEVAL_K=5
  SIMILARITY_THRESHOLD=0.7
  EMBEDDING_PROVIDER="openai"                 # openai or huggingface
  LLM_PROVIDER="openai"                       # openai or huggingface
  EMBEDDING_MODEL="text-embedding-ada-002"    # text-embedding-ada-002 or model sentence-transformers/all-MiniLM-L6-v2
  LLM_MODEL="gpt-4-turbo"                     # gpt-3.5-turbo or gpt-4-turbo or distilbert-base-cased-distilled-squad
  ```

- **Better Prompt Engineering:**
  - In `_generate_llm_response` (see `rag_pipeline.py`), the prompt is improved: if an answer can be calculated manually from data in the context, the model is instructed to do the math and show the steps (with LaTeX/markdown), always showing the final result in bold at the top.

- **Knowledge Base State Hook:**
  - Added a `useKnowledgeBase` React hook in the frontend to handle state changes when PDF processing/batching is done, so the chat interface is only enabled when knowledge base is ready.

- **Component-level Styling:**
  - Styling for each React component (chat, file upload, etc) is implemented as a CSS module for better maintainability.

---
