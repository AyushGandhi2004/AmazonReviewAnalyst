# Amazon Competitor Review Analytics Tool

An AI-powered web application that lets Amazon sellers paste their product ASIN and up to 3 competitor ASINs to receive a full competitive analysis report backed by real customer review data.

## What it does

1. Scrapes product metadata (price, rating, BSR, bullet points) via ScrapingBee
2. Collects up to 100 customer reviews per product via Apify
3. Embeds reviews into ChromaDB for semantic search (RAG)
4. Runs structured LLM analysis via Groq (llama-3.3-70b-versatile)
5. Generates a side-by-side competitor comparison with actionable seller recommendations
6. Exports a downloadable PDF report

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI + SSE (live progress) |
| Orchestration | LangChain |
| LLM | Groq — llama-3.3-70b-versatile |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | ChromaDB (local) |
| Product Scraper | ScrapingBee |
| Review Scraper | Apify — junglee/amazon-reviews-scraper |
| PDF | WeasyPrint + Jinja2 |
| UI (Phase 1) | Streamlit |
| UI (Phase 2) | React + Vite + Tailwind CSS |

## Project Structure

```
amazon-review-analyzer/
├── backend/
│   ├── main.py              # FastAPI app + all routes
│   ├── config.py            # Settings loaded from .env
│   ├── models.py            # Pydantic request/response schemas
│   ├── scraper/
│   │   ├── listing_scraper.py   # ScrapingBee integration
│   │   └── review_scraper.py    # Apify integration
│   ├── pipeline/
│   │   ├── embeddings.py        # SentenceTransformer + ChromaDB
│   │   ├── rag.py               # Semantic query logic
│   │   └── llm_chain.py         # LangChain chains + Groq
│   ├── report/
│   │   ├── assembler.py         # Combines all outputs into report
│   │   └── pdf_generator.py     # WeasyPrint PDF export
│   ├── templates/
│   │   └── report.html          # Jinja2 HTML template for PDF
│   └── utils/
│       ├── sse.py               # SSE event helpers
│       └── validators.py        # ASIN format validation
├── streamlit_app/
│   └── app.py               # Streamlit UI (Phase 1)
├── .env                     # Your API keys (never commit)
├── .env.example             # Key template
├── requirements.txt
└── README.md
```

## Setup

### Backend runtime note

The backend embeddings pipeline uses SentenceTransformers with the default PyTorch backend, so TensorFlow is not required for deployment.

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd amazon-review-analyzer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Required keys:
- `SCRAPINGBEE_API_KEY` — [scrapingbee.com](https://www.scrapingbee.com/)
- `APIFY_API_TOKEN` — [apify.com](https://apify.com/)
- `GROQ_API_KEY` — [console.groq.com](https://console.groq.com/)

### 3. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 4. Start the Streamlit UI

```bash
streamlit run streamlit_app/app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Start analysis, returns `run_id` |
| `GET` | `/api/progress/{run_id}` | SSE stream of live progress |
| `GET` | `/api/report/{run_id}` | Full report JSON |
| `GET` | `/api/report/{run_id}/pdf` | PDF file download |
| `GET` | `/api/health` | Health check |

### Example usage

```bash
# Start analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"your_asin": "B08N5WRWNW", "competitor_asins": ["B07XJ8C8F5"]}'

# Stream progress
curl -N http://localhost:8000/api/progress/<run_id>

# Get report
curl http://localhost:8000/api/report/<run_id>
```

