# Run the data processing pipeline locally on Windows
# This script starts both the API server and Streamlit UI

Write-Host "🚀 Starting Mini Telemetry Pipeline locally..." -ForegroundColor Green

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start API server in background
Write-Host "Starting API server on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\.venv\Scripts\Activate.ps1; uvicorn src.api:app --reload"

# Wait a moment for API to start
Start-Sleep -Seconds 3

# Start Streamlit
Write-Host "Starting Streamlit UI on http://localhost:8501..." -ForegroundColor Cyan
streamlit run streamlit_app.py
