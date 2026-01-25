# 🚀 Quick Start Guide

## Your API Server is Already Running! ✅

The API is live at: **http://localhost:8000**

---

## 📖 3 Ways to Use the Pipeline

### **1️⃣ Interactive API Docs (EASIEST)**

Open your browser and visit:
**http://localhost:8000/docs**

This gives you a beautiful Swagger UI where you can:
- Click any endpoint to expand it
- Click "Try it out"
- Fill in parameters
- Click "Execute"
- See the response

### **2️⃣ Python Script (test_api.py)**

Already created for you! Just run:

```bash
python test_api.py
```

This will:
- Ingest 2 new logs with PII (email, IP, API key)
- Search for "payment failed"
- Show logs from "payment-service" source

### **3️⃣ Streamlit UI (Install First)**

```bash
pip install streamlit
streamlit run streamlit_app.py
```

Then open the URL it shows (usually http://localhost:8501)

---

## 🎯 Common Tasks

### **Search for Similar Logs**

**Browser:**
Go to http://localhost:8000/docs → `/search` → Try it out
- q: "database error"
- k: 5

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/search?q=database+error&k=5" -UseBasicParsing | Select-Object -ExpandProperty Content
```

### **Get Log Summary**

**Browser:**
http://localhost:8000/summary

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/summary" -UseBasicParsing | Select-Object -ExpandProperty Content
```

### **Ingest New Logs**

**Python:**
```python
import requests

new_logs = [
    {
        "timestamp": "2024-01-25T15:30:00Z",
        "level": "ERROR",
        "message": "Connection timeout to 10.0.0.5"
    }
]

response = requests.post(
    "http://localhost:8000/ingest?source=my-service",
    json=new_logs
)
print(response.json())
```

**Browser:**
Go to http://localhost:8000/docs → `/ingest` → Try it out

### **Filter by Source**

```python
import requests

# Get only logs from "payment-service"
response = requests.get("http://localhost:8000/logs?source=payment-service")
print(response.json())
```

---

## 📊 What's Happening Behind the Scenes

1. **PII Masking**: Emails, IPs, and API keys are automatically masked
   - `user@email.com` → `[EMAIL]`
   - `192.168.1.1` → `[IP]`
   - `api_key=secret` → `[TOKEN]`

2. **Smart Filtering**: DEBUG logs and heartbeat messages are removed

3. **Semantic Search**: Your query is converted to a vector and matched using AI
   - "database error" finds "DB timeout", "connection failed", etc.

4. **Auto-Save**: Every ingestion automatically saves to disk
   - Logs: `models/logs.pkl`
   - Index: `models/faiss.index`

---

## 🔍 Example Searches to Try

- "authentication failed"
- "high memory"
- "connection error"
- "disk space"
- "slow query"

The AI understands meaning, not just keywords!

---

## 🐳 Docker Usage (Optional)

```bash
# Build
docker build -t databahn-pipeline .

# Run
docker run -p 8000:8000 databahn-pipeline
```

---

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal running uvicorn

---

## 💡 Pro Tips

1. **API Docs First**: Always start with http://localhost:8000/docs - it's the easiest way to explore
2. **Source Tags**: Tag your logs by source to filter later (e.g., "webapp", "api", "database")
3. **Semantic Search**: Use natural language queries - the AI understands context
4. **Check Data**: Your current logs are in `models/logs.pkl` and searchable via `/search`
