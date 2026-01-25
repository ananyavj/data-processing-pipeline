#!/bin/bash
# Run the data processing pipeline locally on Mac/Linux
# This script starts both the API server and Streamlit UI

echo "🚀 Starting Mini Telemetry Pipeline locally..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start API server in background
echo "Starting API server on http://localhost:8000..."
uvicorn src.api:app --reload &

# Wait a moment for API to start
sleep 3

# Start Streamlit
echo "Starting Streamlit UI on http://localhost:8501..."
streamlit run streamlit_app.py
