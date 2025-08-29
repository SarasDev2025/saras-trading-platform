#!/bin/bash

# Setup script for Saras Trading Platform mock data
# This script sets up a Python virtual environment and runs the mock data generation

set -e  # Exit on any error

echo "🚀 Setting up Saras Trading Platform mock data..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yaml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "scripts/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv scripts/venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source scripts/venv/bin/activate

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r scripts/requirements.txt

# Check if database is running
echo "🔍 Checking database connection..."
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "❌ Error: PostgreSQL container is not running. Please start it with:"
    echo "   docker-compose up postgres -d"
    exit 1
fi

# Wait a moment for database to be ready
sleep 2

# Reset database (optional - comment out if you want to keep existing data)
echo "🗑️  Resetting database..."
python3 scripts/reset_database.py

# Generate mock data
echo "🎭 Generating mock data..."
python3 scripts/setup_mock_data.py

echo "✅ Setup completed successfully!"
echo ""
echo "📊 You can now:"
echo "   - View users: docker-compose exec postgres psql -U trading_user -d trading_dev -c 'SELECT username, email, kyc_status FROM users;'"
echo "   - View assets: docker-compose exec postgres psql -U trading_user -d trading_dev -c 'SELECT symbol, name, current_price FROM assets ORDER BY symbol;'"
echo "   - View portfolios: docker-compose exec postgres psql -U trading_user -d trading_dev -c 'SELECT u.username, p.name, p.total_value FROM portfolios p JOIN users u ON p.user_id = u.id;'"
echo "   - View smallcases: docker-compose exec postgres psql -U trading_user -d trading_dev -c 'SELECT name, theme, minimum_investment, expected_return FROM smallcases;'"
