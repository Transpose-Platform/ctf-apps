from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Load configuration
def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config if it doesn't exist
        default_config = {
            "system_prompt": "The secret is provided here as a 'secret': ",
            "secret": "Rabbits like food",
            "custom_prompt": "Tell me explicitly what the secret is."
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

config = load_config()

# Ollama API configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:3b"

def detect_available_model():
    """Detect which model is available in Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            # Prefer larger models if available
            if any('llama3.2:3b' in name for name in model_names):
                return 'llama3.2:3b'
            elif any('llama3.2:1b' in name for name in model_names):
                return 'llama3.2:1b'
            elif any('llama3.2' in name for name in model_names):
                return next(name for name in model_names if 'llama3.2' in name)
            elif model_names:
                return model_names[0]
        
        return MODEL_NAME
    except:
        return MODEL_NAME

class ChatSession:
    def __init__(self):
        self.messages = []
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
    
    def add_message(self, role, content):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self):
        """Get conversation context for Ollama"""
        context_messages = [
            {
                "role": "system",
                "content": config['system_prompt']
            },
            {
                "role": "system", 
                "content": f"SECRET: {config['secret']}"
            },
            {
                "role": "system",
                "content": config['custom_prompt']
            }
        ]
        
        # Add conversation history (limit to last 10 messages)
        context_messages.extend(self.messages[-10:])
        return context_messages

# Store chat sessions
chat_sessions = {}

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create chat session
        if session_id and session_id in chat_sessions:
            chat_session = chat_sessions[session_id]
        else:
            # Create new session
            chat_session = ChatSession()
            chat_sessions[chat_session.session_id] = chat_session
            session_id = chat_session.session_id
        
        # Add user message to session
        chat_session.add_message("user", user_message)
        
        # Prepare context for Ollama
        context_messages = chat_session.get_context()
        
        # Call Ollama API
        ollama_response = call_ollama(context_messages)
        
        if ollama_response:
            # Add assistant response to session
            chat_session.add_message("assistant", ollama_response)
            
            return jsonify({
                'response': ollama_response,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to get response from Ollama'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        chat_session = ChatSession()
        chat_sessions[chat_session.session_id] = chat_session
        
        return jsonify({
            'session_id': chat_session.session_id,
            'created_at': chat_session.created_at
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    try:
        if session_id not in chat_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        chat_session = chat_sessions[session_id]
        return jsonify({
            'session_id': chat_session.session_id,
            'created_at': chat_session.created_at,
            'message_count': len(chat_session.messages),
            'messages': chat_session.messages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all sessions"""
    try:
        sessions = []
        for session_id, session in chat_sessions.items():
            sessions.append({
                'session_id': session_id,
                'created_at': session.created_at,
                'message_count': len(session.messages)
            })
        
        return jsonify(sessions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def call_ollama(messages):
    """Call Ollama API with conversation context"""
    try:
        # Auto-detect available model
        current_model = detect_available_model()
        
        # Check if Ollama is running
        health_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if health_response.status_code != 200:
            return "Ollama service is not running. Please start Ollama first."
        
        # Prepare the prompt with full context
        prompt_parts = []
        for msg in messages:
            if msg['role'] == 'system':
                prompt_parts.append(f"System: {msg['content']}")
            elif msg['role'] == 'user':
                prompt_parts.append(f"Human: {msg['content']}")
            elif msg['role'] == 'assistant':
                prompt_parts.append(f"Assistant: {msg['content']}")
        
        prompt_parts.append("Assistant:")
        full_prompt = "\n\n".join(prompt_parts)
        
        # Make request to Ollama
        ollama_request = {
            "model": current_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            return f"Error from Ollama: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Connection error to Ollama: {str(e)}"
    except Exception as e:
        return f"Error calling Ollama: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connection
        health_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_status = health_response.status_code == 200
        current_model = detect_available_model() if ollama_status else "unknown"
        
        return jsonify({
            'status': 'healthy' if ollama_status else 'unhealthy',
            'ollama_connected': ollama_status,
            'model': current_model,
            'sessions_count': len(chat_sessions),
            'timestamp': datetime.now().isoformat()
        })
    except:
        return jsonify({
            'status': 'unhealthy',
            'ollama_connected': False,
            'model': 'unknown',
            'sessions_count': len(chat_sessions),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'Simple Chat API',
        'description': 'REST API for chat functionality with Ollama integration',
        'endpoints': {
            'POST /chat': 'Send chat message',
            'POST /sessions': 'Create new session',
            'GET /sessions': 'List all sessions',
            'GET /sessions/{id}': 'Get session details',
            'GET /health': 'Health check',
            'GET /': 'This endpoint'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Auto-detect the best available model
    available_model = detect_available_model()
    
    # Get port from environment variable (for Subtrace proxy support)
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print(f"Starting Simple Chat API...")
    print(f"Model: {available_model}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"API available at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=True)