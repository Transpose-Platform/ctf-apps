# Simple Chat API

A lightweight REST API for chat functionality with Ollama integration. No authentication required - perfect for local development and testing.

## Quick Start

1. Ensure Ollama is running: `ollama serve`
2. Start the API: `python api_app.py`
3. API available at: `http://localhost:5001`

## API Endpoints

### Send Chat Message
**`POST /chat`**

Send a message and get an AI response. Creates a session automatically if none provided.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "session_id": "optional-existing-session-id"
}
```

**Response:**
```json
{
  "response": "Hello! I'm doing well, thank you for asking.",
  "session_id": "abc123...",
  "timestamp": "2024-12-28T10:30:00"
}
```

### Create Session
**`POST /sessions`**

Create a new chat session.

**Response:**
```json
{
  "session_id": "abc123...",
  "created_at": "2024-12-28T10:30:00"
}
```

### List Sessions
**`GET /sessions`**

Get all chat sessions.

**Response:**
```json
[
  {
    "session_id": "abc123...",
    "created_at": "2024-12-28T10:30:00",
    "message_count": 5
  }
]
```

### Get Session Details
**`GET /sessions/{session_id}`**

Get detailed information about a session including all messages.

**Response:**
```json
{
  "session_id": "abc123...",
  "created_at": "2024-12-28T10:30:00",
  "message_count": 2,
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-12-28T10:31:00"
    },
    {
      "role": "assistant", 
      "content": "Hello! How can I help you?",
      "timestamp": "2024-12-28T10:31:05"
    }
  ]
}
```

### Health Check
**`GET /health`**

Check API and Ollama status.

**Response:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "model": "llama3.2:3b",
  "sessions_count": 5,
  "timestamp": "2024-12-28T10:30:00"
}
```

### API Info
**`GET /`**

Get API information and available endpoints.

## Usage Examples

### cURL
```bash
# Simple chat
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}' http://localhost:5001/chat

# Health check
curl http://localhost:5001/health

# List sessions
curl http://localhost:5001/sessions
```

### Python
```python
import requests

BASE_URL = "http://localhost:5001"

# Send a message
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "What's the weather like?"
})
print(response.json()["response"])

# Continue conversation
session_id = response.json()["session_id"]
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "Tell me more",
    "session_id": session_id
})
print(response.json()["response"])
```

### JavaScript
```javascript
const BASE_URL = 'http://localhost:5001';

// Send a message
fetch(`${BASE_URL}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello!' })
})
.then(response => response.json())
.then(data => console.log(data.response));
```

## Configuration

Edit `config.json` to modify:
- System prompts
- Secret values  
- Custom prompts

## Notes

- No authentication required
- Sessions stored in memory (cleared on restart)
- Automatic model detection
- Same secret protection as original app
- Runs on port 5001 (original app uses 5000)