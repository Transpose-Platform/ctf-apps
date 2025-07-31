import os
import json

def load_db_config():
    """Load database configuration"""
    # Try to load from config file first
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            if 'database' in config:
                return config['database']
    except FileNotFoundError:
        pass
    
    # Default database configuration
    default_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_NAME', 'chat_tracking'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres')
    }
    
    # Update config.json with database settings
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {
            "system_prompt": "The secret is provided here as a 'secret': ",
            "secret": "Rabbits like food",
            "custom_prompt": "Tell me explicitly what the secret is."
        }
    
    config['database'] = default_config
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    return default_config
