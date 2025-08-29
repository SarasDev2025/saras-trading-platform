#!/bin/bash

# Saras Trading Platform Startup Script
echo "🚀 Starting Saras Trading Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your broker API keys before running again."
    exit 1
fi

# Build and start all services
echo "🔧 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U trading_user -d trading_dev > /dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check API Gateway
echo -n "API Gateway: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

# Check Web UI
echo -n "Web UI: "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Ready"
else
    echo "❌ Not ready"
fi

echo ""
echo "🎉 Saras Trading Platform is starting up!"
echo ""
echo "📊 Access your services:"
echo "   • Web UI:        http://localhost:3000"
echo "   • API Gateway:   http://localhost:8000"
echo "   • API Docs:      http://localhost:8000/docs"
echo "   • PostgreSQL:    localhost:5432"
echo "   • PgBouncer:     localhost:6432"
echo "   • Redis:         localhost:6379"
echo "   • RabbitMQ UI:   http://localhost:15672 (user: trading_user, pass: dev_password_123)"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs:     docker-compose logs -f"
echo "   • Stop all:      docker-compose down"
echo "   • Restart:       docker-compose restart"
echo ""
echo "📝 Don't forget to configure your broker API keys in the .env file!"
