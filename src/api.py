#api.py
from fastapi import FastAPI, Body, Query, UploadFile, File, HTTPException
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path

from src.ingest import load_logs as load_logs_file
from src.parser import parse_file
from src.cleaner import clean_logs
from src.embedder import LogEmbedder
from src.indexer import LogIndexer
from src.storage import save_logs, load_logs, save_index, load_index
from src.pii import mask_logs


app = FastAPI()


# ---------- Global state ----------
logs = []  # Will hold all logs in memory
embedder = None
indexer = None


# ---------- Startup: load or build pipeline ----------
@app.on_event("startup")
def startup_event():
    global logs, embedder, indexer
    
    print("Starting up...")
    
    # Load embedder model (always needed)
    embedder = LogEmbedder()
    
    # Try to load saved logs and index
    saved_logs = load_logs()
    saved_index = load_index()
    
    if saved_logs and saved_index:
        # Use saved data
        logs = saved_logs
        indexer = LogIndexer(embeddings=np.zeros((len(logs), 384)), index_path="models/faiss.index")
        indexer.index = saved_index
        print(f"✓ Loaded {len(logs)} logs from disk")
    else:
        # Build new from initial data file
        if os.path.exists("data/raw_logs.json"):
            print("Building new pipeline from data/raw_logs.json...")
            raw_logs = load_logs_file("data/raw_logs.json")
            
            # Clean logs
            cleaned = clean_logs(raw_logs)
            
            # Mask PII before embedding
            masked = mask_logs(cleaned)
            
            # Generate embeddings
            embeddings = embedder.embed_logs(masked)
            
            # Build FAISS index
            indexer = LogIndexer(embeddings, index_path="models/faiss.index")
            
            # Store in memory
            logs = masked
            
            # Save to disk
            save_logs(logs)
            save_index(indexer.index)
            
            print(f"✓ Built and saved {len(logs)} logs")
        else:
            print("⚠ No data found. Starting with empty log store.")
            # Create empty index with dimension 384 (all-MiniLM-L6-v2 output size)
            import faiss
            indexer = LogIndexer(embeddings=np.zeros((0, 384)), index_path="models/faiss.index")


# ---------- Routes ----------

@app.get("/")
def home():
    return {
        "message": "Mini Databahn Pipeline Running",
        "total_logs": len(logs)
    }


@app.get("/logs")
def get_logs(source: str = Query(None)):
    """
    Get all logs, optionally filtered by source.
    """
    if source:
        filtered = [log for log in logs if log.get("source") == source]
        return filtered
    return logs


@app.get("/summary")
def summary(source: str = Query(None)):
    """
    Get log level counts, optionally filtered by source.
    """
    filtered_logs = logs
    if source:
        filtered_logs = [log for log in logs if log.get("source") == source]
    
    counts = {}
    for log in filtered_logs:
        level = log["level"]
        counts[level] = counts.get(level, 0) + 1
    
    return {
        "total": len(filtered_logs),
        "by_level": counts
    }


@app.get("/search")
def search(q: str, source: str = Query(None), k: int = 5):
    """
    Semantic search over logs using FAISS.
    Optionally filter by source.
    """
    # Generate query embedding
    query_vec = embedder.model.encode(q)
    
    # Search FAISS (returns indices)
    indices = indexer.search(query_vec, k=min(k, len(logs)))
    
    # Get corresponding logs
    results = [logs[i] for i in indices if i < len(logs)]
    
    # Filter by source if provided
    if source:
        results = [log for log in results if log.get("source") == source]
    
    return results


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and ingest a raw log file (.log, .txt, or .json).
    
    Steps:
    1. Validate file extension
    2. Save file temporarily
    3. Parse raw logs to JSON format (auto-detect format)
    4. Ingest using existing pipeline
    5. Clean up temp file
    """
    global logs, indexer
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".log", ".txt", ".json"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file_ext}. Only .log, .txt, and .json files are supported."
        )
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Save uploaded file temporarily
    temp_file = None
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb', 
            delete=False, 
            suffix=file_ext,
            dir=uploads_dir
        )
        
        # Write uploaded content
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        
        # Parse raw logs using parser (handles JSON, .log, .txt)
        source_name = file.filename
        parsed_logs = parse_file(temp_file.name, source_name)
        
        # Count lines processed
        with open(temp_file.name, 'r', encoding='utf-8') as f:
            lines_processed = sum(1 for _ in f)
        
        if not parsed_logs:
            return {
                "lines_processed": lines_processed,
                "logs_indexed": 0,
                "source": source_name
            }
        
        # Clean logs
        cleaned = clean_logs(parsed_logs)
        
        if not cleaned:
            return {
                "lines_processed": lines_processed,
                "logs_indexed": 0,
                "source": source_name
            }
        
        # Mask PII
        masked = mask_logs(cleaned)
        
        # Generate embeddings
        new_embeddings = embedder.embed_logs(masked)
        
        # Add to FAISS index
        indexer.index.add(np.array(new_embeddings).astype("float32"))
        
        # Append to in-memory logs
        logs.extend(masked)
        
        # Save to disk
        save_logs(logs)
        save_index(indexer.index)
        
        return {
            "lines_processed": lines_processed,
            "logs_indexed": len(masked),
            "source": source_name
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass  # Ignore cleanup errors


@app.post("/ingest")
def ingest(new_logs: list = Body(...), source: str = Query("unknown")):
    """
    Ingest new logs:
    1. Tag with source
    2. Clean
    3. Mask PII
    4. Embed
    5. Add to FAISS
    6. Append to memory
    7. Save to disk
    """
    global logs, indexer
    
    # Tag each log with source
    for log in new_logs:
        log["source"] = source
    
    # Clean noisy logs
    cleaned = clean_logs(new_logs)
    
    if not cleaned:
        return {"message": "No logs remained after cleaning"}
    
    # Mask PII
    masked = mask_logs(cleaned)
    
    # Generate embeddings
    new_embeddings = embedder.embed_logs(masked)
    
    # Add to FAISS index
    indexer.index.add(np.array(new_embeddings).astype("float32"))
    
    # Append to in-memory logs
    logs.extend(masked)
    
    # Save to disk
    save_logs(logs)
    save_index(indexer.index)
    
    return {
        "message": f"{len(masked)} logs ingested successfully",
        "source": source,
        "total_logs": len(logs)
    }


@app.delete("/clear-all")
def clear_all():
    """
    Delete all saved data from disk and clear memory.
    This removes:
    - Saved logs (models/logs.pkl)
    - FAISS index (models/faiss.index)
    - In-memory logs
    And reinitializes with an empty index.
    """
    global logs, indexer
    
    # List of files to delete
    files_to_delete = [
        "models/logs.pkl",
        "models/faiss.index"
    ]
    
    deleted_files = []
    
    # Delete each file if it exists
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
                print(f"Deleted {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")
    
    # Clear in-memory logs
    logs = []
    
    # Reinitialize FAISS index with empty embeddings
    import faiss
    indexer = LogIndexer(embeddings=np.zeros((0, 384)), index_path="models/faiss.index")
    
    return {
        "message": "All saved data cleared successfully",
        "deleted_files": deleted_files,
        "total_logs": len(logs)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
