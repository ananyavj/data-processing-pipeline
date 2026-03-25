# Data Processing Mini Pipeline

End-to-end log intelligence system with semantic search, PII masking, and REST API.

---

## Problem Statement

Traditional log analysis relies on keyword matching, which fails to capture semantic meaning. Engineers searching for "database connection failed" miss logs containing "db timeout" or "SQL server unreachable" — despite describing the same issue.

This project solves that by:
- **Semantic search** using sentence embeddings (not keyword matching)
- **Automated PII masking** to ensure compliance before indexing
- **Multi-source ingestion** with source tagging for organizational log systems
- **Production-ready architecture** with REST API, persistence, and containerization

---

## Features

- **ETL Pipeline**: Ingestion → Cleaning → PII Masking → Embedding → Indexing
- **Semantic Search**: Vector similarity search using FAISS (384-dim embeddings)
- **PII Protection**: Automatic detection and masking of emails, IPs, credit cards, phone numbers
- **REST API**: FastAPI backend with endpoints for search, ingestion, and log retrieval
- **File Upload**: Upload raw .log/.txt files through UI with automatic parsing and ingestion
- **Web UI**: Streamlit interface for interactive querying
- **Multi-source Support**: Tag and filter logs by source system
- **Persistent Storage**: FAISS index and logs saved to disk (survives restarts)
- **Containerized Deployment**: Docker Compose with multi-service architecture

---

## Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (Port 8501)
│   Web Interface │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   FastAPI       │  (Port 8000)
│   REST Service  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Pipeline    │
│  ├─ Cleaner     │
│  ├─ PII Masker  │
│  ├─ Embedder    │  (sentence-transformers)
│  └─ Indexer     │  (FAISS)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Disk Storage   │
│  ├─ logs.pkl    │
│  └─ faiss.index │
└─────────────────┘
```

**Deployment**: Runs as 2 Docker containers networked via Docker Compose.

---

## Project Structure

```
databahn-mini-pipeline/
├── src/
│   ├── api.py           # FastAPI application (routes + startup)
│   ├── parser.py        # Raw log file parser (.log → JSON)
│   ├── ingest.py        # Load logs from JSON
│   ├── cleaner.py       # Remove noisy/incomplete logs
│   ├── pii.py           # Regex-based PII masking
│   ├── embedder.py      # sentence-transformers wrapper
│   ├── indexer.py       # FAISS index builder + search
│   └── storage.py       # Pickle-based persistence
├── data/
│   └── raw_logs.json    # Initial log data
├── models/
│   ├── logs.pkl         # Persisted logs
│   └── faiss.index      # FAISS vector index
├── streamlit_app.py     # Streamlit UI
├── test_api.py          # API integration tests
├── multi_source_demo.py # Demo script for multi-source ingestion
├── Dockerfile.api       # API container
├── Dockerfile.streamlit # UI container
├── docker-compose.yml   # Orchestration
└── requirements.txt     # Dependencies
```

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| **API**     | FastAPI, Uvicorn                    |
| **UI**      | Streamlit                           |
| **ML**      | sentence-transformers (all-MiniLM-L6-v2) |
| **Search**  | FAISS (CPU)                         |
| **Storage** | Pickle (logs), FAISS index          |
| **Compute** | NumPy, PyTorch (CPU)                |
| **Deploy**  | Docker, Docker Compose              |

---

## How It Works

### Data Flow (Ingestion → Search)

1. **Ingest**: Raw logs loaded from JSON or POSTed via API
2. **Tag**: Each log tagged with source identifier
3. **Clean**: Filter out noisy logs (e.g., missing fields, debug spam)
4. **Mask PII**: Detect and replace emails, IPs, phone numbers, SSNs
5. **Embed**: Generate 384-dim vectors using sentence-transformers
6. **Index**: Add embeddings to FAISS vector database
7. **Persist**: Save logs and FAISS index to disk
8. **Search**: User query → embedded → FAISS retrieves k-nearest neighbors

### Search Example

**Query**: `"database connection error"`

**Traditional keyword search** would miss:
- "db timed out after 30s"
- "SQL server unreachable"

**Semantic search** returns all semantically similar logs, regardless of exact wording.

---

## How to Run

### Prerequisites

- Docker
- Docker Compose

### Start the System

```bash
docker compose up
```

This starts:
- **API**: http://localhost:8000
- **UI**: http://localhost:8501

### Stop the System

```bash
docker compose down
```

---

## Running Locally (Without Docker)

For faster development iteration or recruiter testing, you can run the pipeline locally without Docker.

### Prerequisites

- Python 3.8+
- pip

### Option 1: Quick Start (Recommended)

**Windows:**
```powershell
.\run_local.ps1
```

**Mac/Linux:**
```bash
chmod +x run_local.sh
./run_local.sh
```

This automatically:
1. Creates a virtual environment
2. Installs dependencies
3. Starts both API and Streamlit

### Option 2: Manual Setup

1. **Create and activate virtual environment:**

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Start API server** (in one terminal):

```bash
uvicorn src.api:app --reload
```

4. **Start Streamlit UI** (in another terminal):

```bash
streamlit run streamlit_app.py
```

### Access Points

- **API**: http://localhost:8000
- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

---


## API Usage

### 1. Health Check

```bash
curl http://localhost:8000/
```

**Response**:
```json
{
  "message": "Mini Databahn Pipeline Running",
  "total_logs": 150
}
```

### 2. Search Logs (Semantic)

```bash
curl "http://localhost:8000/search?q=database%20error&k=3"
```

**Response**:
```json
[
  {
    "timestamp": "2026-01-20T14:23:11Z",
    "level": "ERROR",
    "message": "Connection to db timed out",
    "source": "api-server"
  },
  ...
]
```

### 3. Filter by Source

```bash
curl "http://localhost:8000/search?q=timeout&source=payment-gateway&k=5"
```

### 4. Upload Log File

```bash
curl -X POST http://localhost:8000/upload-file \
  -F "file=@auth.log"
```

**Response**:
```json
{
  "message": "Successfully uploaded and ingested 15 logs from auth.log",
  "source": "auth.log",
  "logs_ingested": 15,
  "total_logs": 135
}
```

Supported formats:
- ISO 8601: `2024-01-25T10:00:00Z INFO Application started`
- Bracketed: `[2024-01-25 10:00:00] INFO: Database connected`
- Syslog: `Jan 25 10:00:00 ERROR Connection failed`

### 5. Ingest New Logs (JSON)

```bash
curl -X POST http://localhost:8000/ingest?source=nginx \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp": "2026-01-25T10:00:00Z", "level": "ERROR", "message": "502 Bad Gateway"}
  ]'
```

**Response**:
```json
{
  "message": "1 logs ingested successfully",
  "source": "nginx",
  "total_logs": 151
}
```

### 6. Get Log Summary

```bash
curl "http://localhost:8000/summary"
```

**Response**:
```json
{
  "total": 151,
  "by_level": {
    "ERROR": 45,
    "WARN": 32,
    "INFO": 74
  }
}
```

---

## Future Improvements

| Enhancement         | Impact                                      |
|---------------------|---------------------------------------------|
| **Redis Cache**     | Cache search results for repeated queries  |
| **Async Batching**  | Process ingestion in batches for throughput |
| **Kafka Ingestion** | Real-time streaming from distributed systems |
| **Multi-stage Builds** | Reduce Docker image size (1.2GB → 400MB) |
| **Health Checks**   | `/health` and `/ready` endpoints for k8s    |
| **Structured Logging** | Use structured JSON logs for observability |
| **Metrics**         | Prometheus metrics (search latency, requests/sec) |

