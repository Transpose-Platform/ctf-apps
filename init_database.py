#!/usr/bin/env python3
"""
Database Initialization Script for Chat Tracking
"""

import sys
import os
import psycopg2
from db_config import load_db_config

def create_database():
    """Create the chat_tracking database if it doesn't exist"""
    config = load_db_config()
    
    # Connect to PostgreSQL server (not specific database)
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (config['database'],)
            )
            
            if not cursor.fetchone():
                print(f"Creating database '{config['database']}'...")
                cursor.execute(f'CREATE DATABASE "{config["database"]}"')
                print(f"✓ Database '{config['database']}' created successfully")
            else:
                print(f"✓ Database '{config['database']}' already exists")
        
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def initialize_schema():
    """Initialize database schema"""
    config = load_db_config()
    
    try:
        # Read SQL schema file
        with open('database_setup.sql', 'r') as f:
            schema_sql = f.read()
        
        # Connect to the chat_tracking database
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        with conn.cursor() as cursor:
            # Execute schema creation
            cursor.execute(schema_sql)
            conn.commit()
            print("✓ Database schema initialized successfully")
        
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error initializing schema: {e}")
        return False
    except FileNotFoundError:
        print("✗ Error: database_setup.sql file not found")
        return False

def test_connection():
    """Test database connection and verify tables"""
    from database import ChatDatabase
    
    try:
        chat_db = ChatDatabase()
        if chat_db.test_connection():
            print("✓ Database connection test successful")
            
            # Test basic operations
            session_count = chat_db.get_session_count()
            message_count = chat_db.get_message_count()
            
            print(f"✓ Current sessions: {session_count}")
            print(f"✓ Current messages: {message_count}")
            return True
        else:
            print("✗ Database connection test failed")
            return False
            
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        return False

def main():
    """Main initialization function"""
    print("=== Chat Tracking Database Initialization ===")
    print()
    
    # Load configuration
    config = load_db_config()
    print(f"Database configuration:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    print()
    
    # Step 1: Create database
    if not create_database():
        print("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Initialize schema
    if not initialize_schema():
        print("Failed to initialize schema. Exiting.")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_connection():
        print("Connection test failed. Exiting.")
        sys.exit(1)
    
    print()
    print("✓ Database initialization completed successfully!")
    print("✓ Chat tracking is ready to use")

if __name__ == "__main__":
    main()
