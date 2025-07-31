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
# Set Subtrace token if not already set
if [ -z "$SUBTRACE_TOKEN" ]; then
    export SUBTRACE_TOKEN=subt_ENlcnzXj0MfTLYwUDDzOBaRQt2CGbOxKOzjST2lG4cn
fi

echo "Press Ctrl+C to stop the server"
echo "=========================="

# Check if subtrace is available
if command -v subtrace &> /dev/null; then
    echo "Starting API with Subtrace monitoring..."
    
    # Detect OS for appropriate subtrace command
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use subtrace proxy with port forwarding
        echo "macOS detected - using subtrace proxy (5001:5101)"
        echo "Users can still access: http://localhost:5001"
        
        # Start subtrace proxy in background
        subtrace proxy 5001:5101 &
        PROXY_PID=$!
        sleep 2
        
        # Start Flask API on internal port 5101
        export FLASK_PORT=5101
        python api_app.py
        
        # Cleanup proxy on exit
        kill $PROXY_PID 2>/dev/null
    else
        # Linux and others - use subtrace run (original port 5001)
        echo "Linux detected - using subtrace run"
        export FLASK_PORT=5001
        subtrace run -- python api_app.py
    fi
else
    echo "Subtrace not found, starting without monitoring..."
    echo "(Run ./setup_ollama.sh to install Subtrace)"
    # Start the API server normally on original port
    export FLASK_PORT=5001
    python api_app.py
fi