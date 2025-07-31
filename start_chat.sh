#!/bin/bash

# Cross-platform startup script for Chat Assistant
echo "=== Starting AI Chat Assistant ==="
echo ""

# Detect operating system
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo "Operating System: $OS"

# Function to check if Ollama is running
check_ollama() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if Ollama is running
echo "Checking Ollama status..."
if check_ollama; then
    echo "✓ Ollama is running"
else
    echo "Ollama is not running. Starting it..."
    
    if [[ "$OS" == "linux" ]]; then
        # Try systemctl first (Linux/Raspberry Pi)
        if command -v systemctl &> /dev/null; then
            sudo systemctl start ollama
            sleep 5
            
            if ! check_ollama; then
                echo "Systemctl failed, starting manually..."
                ollama serve &
                sleep 5
            fi
        else
            echo "Starting Ollama manually..."
            ollama serve &
            sleep 5
        fi
    elif [[ "$OS" == "macos" ]]; then
        # Try brew services first (macOS)
        if command -v brew &> /dev/null; then
            brew services start ollama 2>/dev/null
            sleep 3
        fi
        
        if ! check_ollama; then
            echo "Starting Ollama manually..."
            ollama serve &
            sleep 5
        fi
    fi
    
    # Final check
    if check_ollama; then
        echo "✓ Ollama started successfully"
    else
        echo "✗ Failed to start Ollama. Please start it manually with: ollama serve"
        exit 1
    fi
fi

# Detect available model
echo "Checking for available models..."
AVAILABLE_MODELS=$(ollama list)

if echo "$AVAILABLE_MODELS" | grep -q "llama3.2:3b"; then
    MODEL="llama3.2:3b"
    echo "✓ Using llama3.2:3b model"
elif echo "$AVAILABLE_MODELS" | grep -q "llama3.2:1b"; then
    MODEL="llama3.2:1b"
    echo "✓ Using llama3.2:1b model"
else
    echo "No suitable model found. Available models:"
    echo "$AVAILABLE_MODELS"
    echo ""
    echo "Please run the setup script first: ./setup_ollama.sh"
    exit 1
fi

# Update the model in app.py if needed
if [ -f "app.py" ]; then
    # Update MODEL_NAME in app.py to match available model
    if grep -q "MODEL_NAME.*=" app.py; then
        sed -i.bak "s/MODEL_NAME = .*/MODEL_NAME = \"$MODEL\"/" app.py
        echo "✓ Updated app.py to use $MODEL"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -q -r requirements.txt

# Get network information
if [[ "$OS" == "linux" ]]; then
    # Linux (including Raspberry Pi)
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
elif [[ "$OS" == "macos" ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n1)
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="localhost"
    fi
else
    LOCAL_IP="localhost"
fi

echo ""
echo "=== Starting Flask Application ==="
echo "Model: $MODEL"
echo "Local access: http://localhost:5000"
if [ "$LOCAL_IP" != "localhost" ]; then
    echo "Network access: http://$LOCAL_IP:5000"
fi
# Set Subtrace token if not already set
if [ -z "$SUBTRACE_TOKEN" ]; then
    export SUBTRACE_TOKEN=subt_ENlcnzXj0MfTLYwUDDzOBaRQt2CGbOxKOzjST2lG4cn
fi

echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Check if subtrace is available
if command -v subtrace &> /dev/null; then
    echo "Starting application with Subtrace monitoring..."
    
    # Detect OS for appropriate subtrace command
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use subtrace proxy with port forwarding
        echo "macOS detected - using subtrace proxy (5000:5100)"
        echo "Users can still access: http://localhost:5000"
        
        # Start subtrace proxy in background
        subtrace proxy 5000:5100 &
        PROXY_PID=$!
        sleep 2
        
        # Start Flask app on internal port 5100
        export FLASK_PORT=5100
        python3 app.py
        
        # Cleanup proxy on exit
        kill $PROXY_PID 2>/dev/null
    else
        # Linux and others - use subtrace run (original port 5000)
        echo "Linux detected - using subtrace run"
        export FLASK_PORT=5000
        subtrace run -- python3 app.py
    fi
else
    echo "Subtrace not found, starting without monitoring..."
    echo "(Run ./setup_ollama.sh to install Subtrace)"
    # Start the Flask application normally on original port
    export FLASK_PORT=5000
    python3 app.py
fi