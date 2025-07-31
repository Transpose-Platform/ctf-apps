#!/bin/bash

# Simple Chat API Startup Script
echo "Starting Simple Chat API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing/updating requirements..."
pip install -r requirements.txt

# Check if Ollama is running
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✓ Ollama is running"
else
    echo "⚠ Warning: Ollama is not running on localhost:11434"
    echo "Please start Ollama with: ollama serve"
    echo "Continuing anyway..."
fi

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "⚠ config.json not found - will be created on first run"
fi

echo ""
echo "Starting Simple Chat API on port 5001..."
echo "API available at: http://localhost:5001"
echo "Health check: http://localhost:5001/health"
echo ""
echo "Quick test:"
echo 'curl -X POST -H "Content-Type: application/json" \'
echo '  -d '"'"'{"message": "Hello!"}'"'"' http://localhost:5001/chat'
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================="

# Start the API server
python api_app.py