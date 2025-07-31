# PostgreSQL Chat Tracking Implementation

## Overview

The chat application has been upgraded to use PostgreSQL for persistent chat tracking. All conversations are now stored in a database and will persist across server restarts.

## Features Implemented

- **Anonymous Sessions**: No user authentication required
- **Persistent Storage**: All chat messages stored in PostgreSQL
- **Automatic Session Management**: Sessions created automatically
- **Database Health Monitoring**: Connection status in health checks
- **Unlimited Storage**: No limits on message history

## Database Schema

### Tables Created
- `chat_sessions`: Stores session metadata (session_id, created_at, updated_at)
- `chat_messages`: Stores individual messages (message_id, session_id, role, content, timestamp)

### Features
- Automatic timestamp updates when messages are added
- Foreign key constraints for data integrity
- Indexes for performance optimization

## Setup Instructions

### 1. Install and Setup PostgreSQL

Run the automated setup script:
```bash
./setup_postgres.sh
```

This script will:
- Install PostgreSQL (if not already installed)
- Create the database and user
- Initialize the database schema
- Install Python dependencies

### 2. Manual Setup (Alternative)

If you prefer manual setup:

**Install PostgreSQL:**
```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database manually
createdb chat_tracking
```

**Initialize Database:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run database initialization
python3 init_database.py
```

### 3. Start Applications

**Start Chat Interface:**
```bash
./start_chat.sh
```
Access at: http://localhost:5000

**Start API Server:**
```bash
./start_api.sh
```
Access at: http://localhost:5001

## Configuration

Database settings are stored in `config.json`:
```json
{
  "database": {
    "host": "localhost",
    "port": "5432",
    "database": "chat_tracking",
    "user": "postgres",
    "password": "postgres"
  }
}
```

## Environment Variables (Optional)

You can override database settings with environment variables:
- `DB_HOST`: Database hostname
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

## Health Check

The health check endpoint now includes database status:
```bash
curl http://localhost:5000/api/health
```

Response includes:
- `database_connected`: Boolean status
- `sessions_count`: Total number of sessions
- `messages_count`: Total number of messages

## API Changes

All existing API endpoints continue to work. New database-backed functionality:
- Sessions persist across server restarts
- Message history is preserved
- Automatic session creation and management

## Files Added/Modified

**New Files:**
- `database_setup.sql`: Database schema
- `database.py`: Database operations and ChatSession class
- `db_config.py`: Database configuration management
- `init_database.py`: Database initialization script
- `setup_postgres.sh`: Automated PostgreSQL setup

**Modified Files:**
- `requirements.txt`: Added psycopg2-binary
- `app.py`: Updated to use database storage
- `api_app.py`: Updated to use database storage
- `config.json`: Added database configuration

## Troubleshooting

**Database Connection Issues:**
1. Ensure PostgreSQL is running: `pg_isready`
2. Check database exists: `psql -l | grep chat_tracking`
3. Verify credentials in `config.json`

**Permission Issues:**
1. Ensure user has database access
2. Check PostgreSQL logs: `tail -f /usr/local/var/log/postgres.log` (macOS)

**Schema Issues:**
1. Re-run initialization: `python3 init_database.py`
2. Check tables exist: `psql chat_tracking -c "\dt"`
