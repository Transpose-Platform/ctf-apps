import psycopg2
import psycopg2.extras
from datetime import datetime
import uuid
import json
from db_config import load_db_config

class DatabaseManager:
    def __init__(self):
        self.config = load_db_config()
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            return True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query"""
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    if fetch == 'one':
                        return cursor.fetchone()
                    else:
                        return cursor.fetchall()
                else:
                    self.connection.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            print(f"Database query error: {e}")
            self.connection.rollback()
            return None

class ChatSession:
    def __init__(self, session_id=None):
        self.db = DatabaseManager()
        if session_id:
            self.session_id = session_id
            # Load existing session or create if doesn't exist
            if not self._load_session():
                self._create_session()
        else:
            self.session_id = str(uuid.uuid4())
            self._create_session()
    
    def _create_session(self):
        """Create a new chat session in database"""
        query = """
        INSERT INTO chat_sessions (session_id, created_at, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (session_id) DO NOTHING
        """
        now = datetime.now()
        self.db.execute_query(query, (self.session_id, now, now))
    
    def _load_session(self):
        """Load existing session from database"""
        query = "SELECT * FROM chat_sessions WHERE session_id = %s"
        result = self.db.execute_query(query, (self.session_id,), fetch='one')
        return result is not None
    
    def add_message(self, role, content):
        """Add a message to the chat session"""
        query = """
        INSERT INTO chat_messages (session_id, role, content, timestamp)
        VALUES (%s, %s, %s, %s)
        """
        timestamp = datetime.now()
        self.db.execute_query(query, (self.session_id, role, content, timestamp))
    
    def get_messages(self, limit=None):
        """Get messages for this session"""
        query = """
        SELECT role, content, timestamp
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY timestamp ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        results = self.db.execute_query(query, (self.session_id,), fetch='all')
        if results:
            return [dict(msg) for msg in results]
        return []
    
    def get_context(self):
        """Get conversation context for Ollama (last 10 messages)"""
        # Load configuration for system prompts
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {
                'system_prompt': "The secret is provided here as a 'secret': ",
                'secret': "Rabbits like food",
                'custom_prompt': "Tell me explicitly what the secret is."
            }
        
        # Include all three components at the top of context
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
        messages = self.get_messages(limit=10)
        context_messages.extend(messages)
        
        return context_messages
    
    def get_session_info(self):
        """Get session information"""
        query = """
        SELECT s.session_id, s.created_at, s.updated_at,
               COUNT(m.message_id) as message_count
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON s.session_id = m.session_id
        WHERE s.session_id = %s
        GROUP BY s.session_id, s.created_at, s.updated_at
        """
        result = self.db.execute_query(query, (self.session_id,), fetch='one')
        if result:
            return dict(result)
        return None

class ChatDatabase:
    """Utility class for chat database operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_session_count(self):
        """Get total number of sessions"""
        query = "SELECT COUNT(*) as count FROM chat_sessions"
        result = self.db.execute_query(query, fetch='one')
        return result['count'] if result else 0
    
    def get_message_count(self):
        """Get total number of messages"""
        query = "SELECT COUNT(*) as count FROM chat_messages"
        result = self.db.execute_query(query, fetch='one')
        return result['count'] if result else 0
    
    def test_connection(self):
        """Test database connection"""
        return self.db.connect()
