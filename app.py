from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

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
# Default model - will be auto-detected or can be overridden
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
                # Return first llama3.2 variant found
                return next(name for name in model_names if 'llama3.2' in name)
            elif model_names:
                # Return first available model
                return model_names[0]
        
        return MODEL_NAME  # fallback to default
    except:
        return MODEL_NAME  # fallback to default

class ChatSession:
    def __init__(self):
        self.messages = []
        self.session_id = str(uuid.uuid4())
    
    def add_message(self, role, content):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self):
        """Get conversation context for Ollama"""
        # Include all three components at the top of context: system_prompt, secret, and custom_prompt
        # The secret is protected by the system prompt and enhanced by the custom prompt
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
        
        # Add conversation history (limit to last 10 messages to manage memory)
        context_messages.extend(self.messages[-10:])
        return context_messages

# Store chat sessions
chat_sessions = {}

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get or create chat session
        session_id = session.get('chat_session_id')
        if session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            session['chat_session_id'] = session_id
            chat_sessions[session_id] = ChatSession()
        
        chat_session = chat_sessions[session_id]
        
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
                'session_id': session_id
            })
        else:
            return jsonify({'error': 'Failed to get response from Ollama'}), 500
            
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

@app.route('/api/config')
def get_config():
    """Get current configuration (excluding secret)"""
    safe_config = {
        'system_prompt': config['system_prompt'],
        'custom_prompt': config['custom_prompt'],
        'model': detect_available_model()
    }
    return jsonify(safe_config)

@app.route('/api/health')
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
            'platform': os.name,
            'timestamp': datetime.now().isoformat()
        })
    except:
        return jsonify({
            'status': 'unhealthy',
            'ollama_connected': False,
            'model': 'unknown',
            'platform': os.name,
            'timestamp': datetime.now().isoformat()
        })

if __name__ == '__main__':
    # Auto-detect the best available model
    available_model = detect_available_model()
    
    print(f"Starting AI Chat Application...")
    print(f"Platform: {os.name}")
    print(f"Model: {available_model}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Config loaded: System prompt length = {len(config['system_prompt'])} chars")
    
    app.run(host='0.0.0.0', port=5000, debug=True)