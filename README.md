# AI Chat Assistant with Ollama

A cross-platform Flask web application that provides a chat interface to interact with AI models via Ollama. Supports macOS, Linux, and Raspberry Pi.

## Features

- **Cross-platform support**: Works on macOS, Linux, and Raspberry Pi
- **Responsive web chat interface**: Clean, modern UI that works on desktop and mobile
- **Ollama integration**: Local AI model inference with automatic model detection
- **Conversation context management**: Maintains chat history for contextual responses
- **Configurable system prompts**: Customize AI behavior through configuration file
- **Health monitoring**: Real-time status indicators and API endpoints
- **Auto-optimization**: Automatically selects appropriate model based on platform

## Project Structure

```
hackathon-rl2/
├── app.py                 # Main Flask application
├── config.json           # Configuration file with prompts and secret
├── templates/
│   └── chat.html         # Chat interface template
├── requirements.txt      # Python dependencies
├── setup_ollama.sh      # Cross-platform Ollama installation script
├── start_chat.sh        # Cross-platform application startup script
└── README.md            # This file
```

## Configuration File (config.json)

The application uses a hardcoded configuration file with three main components:

```json
{
  "system_prompt": "Base system instructions for the AI",
  "secret": "Your secret key for the application", 
  "custom_prompt": "Additional prompt text you can modify"
}
```

- **system_prompt**: Core instructions that define the AI's behavior
- **secret**: A secret key that can be used for authentication or other security purposes
- **custom_prompt**: Additional instructions that are appended to the system prompt

## Platform Support

### Model Selection by Platform
- **macOS (Apple Silicon)**: `llama3.2:3b` - Optimized for M1/M2/M3 chips
- **macOS (Intel)**: `llama3.2:3b` - Good performance on modern Intel Macs
- **Linux (x86_64)**: `llama3.2:3b` - Full-featured model for desktop Linux
- **Raspberry Pi (ARM)**: `llama3.2:1b` - Lightweight model optimized for Pi performance

### Prerequisites by Platform

#### macOS
- macOS 10.15 or later
- Python 3.8 or newer
- 8GB RAM recommended
- Homebrew (optional, for easier installation)

#### Linux (Ubuntu/Debian/etc.)
- Ubuntu 18.04+ or equivalent
- Python 3.8 or newer
- 4GB RAM minimum, 8GB recommended
- sudo access for system package installation

#### Raspberry Pi
- Raspberry Pi 4 or 5 (recommended)
- Raspberry Pi OS (64-bit recommended)
- At least 4GB RAM (8GB recommended)
- MicroSD card with at least 16GB free space

## Setup Instructions

### 1. Install Ollama and AI Model

The setup script automatically detects your platform and installs the appropriate model:

```bash
chmod +x setup_ollama.sh
./setup_ollama.sh
```

**What the script does:**
- Detects your operating system (macOS, Linux, Raspberry Pi)
- Installs Ollama using the best method for your platform
- Downloads the optimal AI model for your hardware
- Configures Ollama as a system service (Linux) or user service (macOS)
- Tests the installation

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Or if you prefer using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start the Application

#### Option A: Use the startup script (recommended)
```bash
chmod +x start_chat.sh
./start_chat.sh
```

#### Option B: Direct Python execution
```bash
python3 app.py
```

### 4. Access the Chat Interface

Open a web browser and navigate to:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://[YOUR_IP_ADDRESS]:5000`

The startup script will display your network IP for easy access from other devices.

## Usage

1. **Chat Interface**: Type messages in the input field and press Enter or click Send
2. **Status Indicator**: Green dot indicates Ollama is connected and ready
3. **Conversation Context**: The AI maintains conversation history for context
4. **Model Information**: The interface shows which model is currently being used
5. **Configuration**: Modify `config.json` to customize prompts (restart required)

## API Endpoints

- `GET /` - Main chat interface
- `POST /api/chat` - Send chat messages and receive responses
- `GET /api/config` - Get current configuration (excludes secret)
- `GET /api/health` - Health check and system status

## Customizing the AI Behavior

Edit the `config.json` file to modify:

1. **System Prompt**: Change the AI's base personality and instructions
2. **Custom Prompt**: Add specific behaviors, knowledge domains, or response styles
3. **Secret**: Update the application secret for security purposes

Example configuration:
```json
{
  "system_prompt": "You are a helpful coding assistant specializing in Python and web development.",
  "secret": "my-secure-secret-key",
  "custom_prompt": "Always provide code examples when explaining programming concepts."
}
```

After editing, restart the Flask application to apply changes.

## Platform-Specific Commands

### macOS
```bash
# Check if Ollama is running
pgrep ollama

# Start/stop Ollama service (if installed via Homebrew)
brew services start ollama
brew services stop ollama

# Manual start
ollama serve
```

### Linux/Raspberry Pi
```bash
# Check Ollama service status
sudo systemctl status ollama

# Start/stop/restart Ollama service
sudo systemctl start ollama
sudo systemctl stop ollama
sudo systemctl restart ollama

# View service logs
sudo journalctl -u ollama -f

# Manual start
ollama serve
```

### Universal Commands
```bash
# List installed models
ollama list

# Pull a new model
ollama pull model-name

# Test a model directly
echo "Hello" | ollama run llama3.2:1b
```

## Troubleshooting

### Ollama Not Connected
1. **Check if Ollama is running**:
   - macOS: `pgrep ollama`
   - Linux: `sudo systemctl status ollama`

2. **Start Ollama**:
   - macOS: `brew services start ollama` or `ollama serve`
   - Linux: `sudo systemctl start ollama` or `ollama serve`

3. **Check logs**:
   - macOS: Look for process output if running manually
   - Linux: `sudo journalctl -u ollama -f`

### Model Not Found
```bash
# List available models
ollama list

# Pull the recommended model for your platform
ollama pull llama3.2:1b  # For Raspberry Pi
ollama pull llama3.2:3b  # For macOS/Linux
```

### Performance Issues
- **Raspberry Pi**: Ensure adequate cooling and consider the 1b model
- **All platforms**: Close unnecessary applications to free up RAM
- **macOS**: Ensure you're using Apple Silicon optimized models when available

### Port Already in Use
```bash
# Find process using port 5000
lsof -t -i:5000

# Kill the process
kill $(lsof -t -i:5000)

# Or change the port in app.py
```

### Installation Issues
- **macOS**: Install Xcode command line tools: `xcode-select --install`
- **Linux**: Ensure you have `curl` and `systemctl` available
- **All platforms**: Check internet connection for model downloads

## Security Considerations

- The application runs on all interfaces (0.0.0.0) for network access
- Consider using a reverse proxy (nginx/Apache) for production deployments
- Update the Flask secret key in production environments
- The secret in config.json can be used for additional authentication layers
- Ollama runs locally, so your conversations stay on your device

## Performance Notes

### Model Information
- **llama3.2:1b**: ~1.3GB, optimized for Raspberry Pi and low-resource environments
- **llama3.2:3b**: ~2.0GB, balanced performance for desktops and modern hardware
- **Context**: Conversation history limited to last 10 messages for memory efficiency

### Hardware Recommendations
- **Minimum**: 4GB RAM, 2GB free disk space
- **Recommended**: 8GB RAM, 5GB free disk space
- **Optimal**: 16GB+ RAM for multiple simultaneous conversations

## Development

To modify the application:

1. **Frontend**: Edit `templates/chat.html` for UI changes
2. **Backend**: Modify `app.py` for functionality changes  
3. **Configuration**: Update `config.json` for prompt changes
4. **Styling**: CSS is embedded in the HTML template
5. **Cross-platform support**: Test changes on multiple platforms

## License

This project is provided as-is for educational and development purposes.