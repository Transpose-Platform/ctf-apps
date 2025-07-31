#!/bin/bash

echo "=== PostgreSQL Setup for Chat Tracking ==="
echo ""

# Detect operating system
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo "Operating System: $OS"

# Function to check if PostgreSQL is running
check_postgres() {
    if pg_isready -q 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Install PostgreSQL if not present
install_postgres() {
    echo "Installing PostgreSQL..."
    
    if [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing PostgreSQL via Homebrew..."
            brew install postgresql@15
            brew services start postgresql@15
            
            # Add to PATH
            echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
            export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
        else
            echo "Homebrew not found. Please install Homebrew first:"
            echo "https://brew.sh"
            exit 1
        fi
    elif [[ "$OS" == "linux" ]]; then
        # Ubuntu/Debian
        if command -v apt-get &> /dev/null; then
            sudo apt update
            sudo apt install -y postgresql postgresql-contrib
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        # RHEL/CentOS/Fedora
        elif command -v yum &> /dev/null; then
            sudo yum install -y postgresql-server postgresql-contrib
            sudo postgresql-setup initdb
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        else
            echo "Unsupported Linux distribution. Please install PostgreSQL manually."
            exit 1
        fi
    fi
}

# Setup PostgreSQL user and database
setup_postgres_user() {
    echo "Setting up PostgreSQL user and database..."
    
    if [[ "$OS" == "macos" ]]; then
        # Create user (if not exists)
        createuser -s postgres 2>/dev/null || echo "User 'postgres' already exists"
        
        # Set password (optional for local development)
        psql -d postgres -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
    elif [[ "$OS" == "linux" ]]; then
        # Switch to postgres user and create user
        sudo -u postgres createuser -s postgres 2>/dev/null || echo "User 'postgres' already exists"
        sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
    fi
}

# Main installation process
main() {
    # Check if PostgreSQL is already installed and running
    if check_postgres; then
        echo "✓ PostgreSQL is already running"
    else
        echo "PostgreSQL not found or not running. Installing..."
        install_postgres
        
        # Wait a moment for service to start
        sleep 3
        
        if check_postgres; then
            echo "✓ PostgreSQL installed and running"
        else
            echo "✗ Failed to start PostgreSQL"
            exit 1
        fi
    fi
    
    # Setup user and permissions
    setup_postgres_user
    
    echo ""
    echo "=== Installing Python Dependencies ==="
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # Install requirements
    pip install -r requirements.txt
    
    echo ""
    echo "=== Initializing Database ==="
    
    # Run database initialization
    python3 init_database.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ PostgreSQL setup completed successfully!"
        echo ""
        echo "Database Configuration:"
        echo "  Host: localhost"
        echo "  Port: 5432"
        echo "  Database: chat_tracking"
        echo "  User: postgres"
        echo "  Password: postgres"
        echo ""
        echo "You can now start the chat application with:"
        echo "  ./start_chat.sh"
        echo ""
        echo "Or start the API with:"
        echo "  ./start_api.sh"
    else
        echo "✗ Database initialization failed"
        exit 1
    fi
}

# Run main function
main
