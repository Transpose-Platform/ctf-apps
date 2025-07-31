#!/bin/bash

# Cross-platform Ollama Setup Script
# Supports macOS, Linux, and Raspberry Pi

echo "=== Cross-Platform Ollama Setup ==="
echo ""

# Detect operating system
OS="unknown"
ARCH=$(uname -m)

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"
echo "Architecture: $ARCH"
echo ""

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo "Ollama is already installed!"
    echo "Version: $(ollama --version)"
    echo ""
    
    # Ask if user wants to continue
    read -p "Do you want to continue with model setup? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
else
    echo "Installing Ollama..."
    
    if [[ "$OS" == "macos" ]]; then
        # macOS installation
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install ollama
        else
            echo "Homebrew not found. Installing via curl..."
            curl -fsSL https://ollama.com/install.sh | sh
        fi
        
        # Start Ollama as a service on macOS
        echo "Starting Ollama service..."
        brew services start ollama 2>/dev/null || {
            echo "Starting Ollama manually..."
            ollama serve &
            OLLAMA_PID=$!
            sleep 5
        }
        
    elif [[ "$OS" == "linux" ]]; then
        # Linux installation (including Raspberry Pi)
        
        # Update system packages for Linux
        if command -v apt &> /dev/null; then
            echo "Updating system packages..."
            sudo apt update && sudo apt upgrade -y
            
            # Install curl if not present
            if ! command -v curl &> /dev/null; then
                echo "Installing curl..."
                sudo apt install -y curl
            fi
        elif command -v yum &> /dev/null; then
            echo "Updating system packages..."
            sudo yum update -y
            
            if ! command -v curl &> /dev/null; then
                echo "Installing curl..."
                sudo yum install -y curl
            fi
        fi
        
        # Install Ollama
        curl -fsSL https://ollama.com/install.sh | sh
        
        # Start Ollama service on Linux
        echo "Starting Ollama service..."
        sudo systemctl start ollama
        sudo systemctl enable ollama
        
        # Wait for service to start
        sleep 10
        
        # Check if service is running
        if ! systemctl is-active --quiet ollama; then
            echo "Warning: Ollama service may not have started properly"
            echo "Trying to start manually..."
            ollama serve &
            OLLAMA_PID=$!
            sleep 5
        fi
    fi
fi

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✓ Ollama is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Timeout waiting for Ollama to start"
        echo "Please check if Ollama is running manually with: ollama serve"
        exit 1
    fi
    sleep 2
done

# Choose appropriate model based on architecture and OS
if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
    if [[ "$OS" == "macos" ]]; then
        # Apple Silicon Mac - can handle larger models
        MODEL="llama3.2:3b"
        echo "Detected Apple Silicon Mac - using llama3.2:3b model"
    else
        # ARM Linux (Raspberry Pi) - use smaller model
        MODEL="llama3.2:1b"
        echo "Detected ARM Linux (Raspberry Pi) - using llama3.2:1b model"
    fi
elif [[ "$ARCH" == "x86_64" ]]; then
    # x86_64 - can handle larger models
    MODEL="llama3.2:3b"
    echo "Detected x86_64 architecture - using llama3.2:3b model"
else
    # Default to smallest model for unknown architectures
    MODEL="llama3.2:1b"
    echo "Unknown architecture - using llama3.2:1b model (lightweight)"
fi

echo ""

# Pull the appropriate model
echo "Pulling $MODEL model (this may take several minutes)..."
ollama pull $MODEL

# Verify the model is available
echo "Verifying model installation..."
if ollama list | grep -q "$MODEL"; then
    echo "✓ $MODEL model successfully installed!"
else
    echo "✗ Failed to install $MODEL model"
    echo "Available models:"
    ollama list
    exit 1
fi

# Test the model
echo ""
echo "Testing the model..."
echo "Human: Hello, can you introduce yourself briefly?" | ollama run $MODEL

echo ""
echo "=== Setup Complete! ==="
echo "OS: $OS ($ARCH)"
echo "Ollama: Running on http://localhost:11434"
echo "Model: $MODEL"
echo ""

if [[ "$OS" == "linux" ]]; then
    echo "Linux commands:"
    echo "  Check status: sudo systemctl status ollama"
    echo "  View logs: sudo journalctl -u ollama -f"
elif [[ "$OS" == "macos" ]]; then
    echo "macOS commands:"
    echo "  Check if running: pgrep ollama"
    echo "  Restart: brew services restart ollama"
fi

echo "  List models: ollama list"
echo "  Manual start: ollama serve"
echo ""
echo "You can now start your Flask application!"
echo "Model to use in config: $MODEL"