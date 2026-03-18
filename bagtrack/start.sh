#!/bin/bash

# BagTrack Quick Start Script
# This script helps set up BagTrack for local development

set -e

echo "========================================="
echo "BagTrack Production Management System"
echo "Quick Start Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python 3 is required but not installed. Aborting."; exit 1; }

# Check MySQL
echo "Checking MySQL..."
if command -v mysql &> /dev/null; then
    echo "MySQL found ✓"
else
    echo "MySQL is not installed. Please install MySQL first."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created ✓"
else
    echo "Virtual environment already exists ✓"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed ✓"

# Create .env file if not exists
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    # Update .env with generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here-generate-a-random-string/$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-key-here-generate-a-random-string/$SECRET_KEY/" .env
    fi
    
    echo ".env file created ✓"
    echo ""
    echo "⚠️  Please edit .env and update MySQL credentials:"
    echo "   - MYSQL_PASSWORD"
    echo "   - MYSQL_USER (if different)"
    echo "   - MYSQL_DB (if different)"
else
    echo ".env file already exists ✓"
fi

# Create upload directories
echo ""
echo "Creating upload directories..."
mkdir -p uploads/production uploads/payments
echo "Upload directories created ✓"

# Database setup prompt
echo ""
echo "========================================="
echo "Database Setup"
echo "========================================="
echo ""
echo "Have you created the MySQL database and imported schema.sql?"
read -p "Enter Y if yes, N if you need instructions: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "To set up the database:"
    echo ""
    echo "1. Login to MySQL:"
    echo "   mysql -u root -p"
    echo ""
    echo "2. Run these commands:"
    echo "   CREATE DATABASE bagtrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    echo "   CREATE USER 'bagtrack_user'@'localhost' IDENTIFIED BY 'your_password';"
    echo "   GRANT ALL PRIVILEGES ON bagtrack_db.* TO 'bagtrack_user'@'localhost';"
    echo "   FLUSH PRIVILEGES;"
    echo "   EXIT;"
    echo ""
    echo "3. Import the schema:"
    echo "   mysql -u bagtrack_user -p bagtrack_db < schema.sql"
    echo ""
    echo "4. Update .env with your database credentials"
    echo ""
    exit 0
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo "1. Make sure .env has correct MySQL credentials"
echo "2. Run: python app.py"
echo "3. Visit: http://localhost:5000"
echo ""
echo "Default login credentials:"
echo "Admin - Phone: 9999999999, Password: admin123"
echo "Worker - Phone: 8888888888, Password: worker123"
echo ""
echo "⚠️  Change these passwords in production!"
echo ""

# Ask if user wants to start the app now
read -p "Start the application now? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo ""
    echo "Starting BagTrack..."
    echo "Press Ctrl+C to stop"
    echo ""
    python app.py
fi
