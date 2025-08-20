#!/bin/bash

# Trading Platform Database Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

check_requirements() {
    log "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        warn ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn "Please edit .env file with your configuration"
            exit 1
        else
            error ".env.example file not found"
        fi
    fi
    
    log "Requirements check passed"
}

setup_directories() {
    log "Setting up directories..."
    
    mkdir -p config
    mkdir -p init-scripts/primary
    mkdir -p init-scripts/trading
    mkdir -p init-scripts/analytics
    mkdir -p logs
    mkdir -p backups
    
    log "Directories created"
}

start_services() {
    log "Starting services..."
    
    # Start infrastructure services first
    docker-compose up -d postgres-primary postgres-trading postgres-analytics redis
    
    # Wait for databases to be ready
    log "Waiting for databases to be ready..."
    sleep 30
    
    # Health check
    for i in {1..30}; do
        if docker-compose exec -T postgres-primary pg_isready -U trading_admin -d trading_primary > /dev/null 2>&1; then
            break
        fi
        if [ $i -eq 30 ]; then
            error "Primary database failed to start"
        fi
        sleep 2
    done
    
    # Start remaining services
    docker-compose up -d
    
    log "All services started successfully"
}

setup_database() {
    log "Setting up databases..."
    
    # Run initial setup scripts
    for db in primary trading analytics; do
        if [ -d "init-scripts/$db" ]; then
            log "Setting up $db database..."
            for script in init-scripts/$db/*.sql; do
                if [ -f "$script" ]; then
                    log "Running script: $(basename $script)"
                    docker-compose exec -T postgres-$db psql -U trading_admin -d trading_$db -f "/docker-entrypoint-initdb.d/$(basename $script)"
                fi
            done
        fi
    done
    
    log "Database setup completed"
}

run_health_checks() {
    log "Running health checks..."
    
    # Check PostgreSQL connections
    databases=("primary:trading_primary" "trading:trading_orders" "analytics:trading_analytics")
    
    for db_info in "${databases[@]}"; do
        IFS=':' read -r service dbname <<< "$db_info"
        if docker-compose exec -T postgres-$service pg_isready -U trading_admin -d $dbname > /dev/null 2>&1; then
            log "✓ PostgreSQL $service is healthy"
        else
            error "✗ PostgreSQL $service is not responding"
        fi
    done
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log "✓ Redis is healthy"
    else
        error "✗ Redis is not responding"
    fi
    
    log "Health checks passed"
}

show_status() {
    log "Service Status:"
    docker-compose ps
    
    echo ""
    log "Connection Information:"
    echo "Primary Database: localhost:5432 (trading_primary)"
    echo "Trading Database: localhost:5433 (trading_orders)"
    echo "Analytics Database: localhost:5434 (trading_analytics)"
    echo "Redis: localhost:6379"
    echo "PgBouncer: localhost:6432"
    echo "Postgres Exporter: localhost:9187"
    
    echo ""
    log "Useful Commands:"
    echo "View logs: docker-compose logs -f [service]"
    echo "Connect to DB: docker-compose exec postgres-primary psql -U trading_admin -d trading_primary"
    echo "Stop services: docker-compose down"
    echo "Backup: ./scripts/backup.sh"
    echo "Restore: ./scripts/restore.sh <backup_file>"
}

create_backup() {
    log "Creating database backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup each database
    databases=("primary:trading_primary" "trading:trading_orders" "analytics:trading_analytics")
    
    for db_info in "${databases[@]}"; do
        IFS=':' read -r service dbname <<< "$db_info"
        log "Backing up $dbname..."
        docker-compose exec -T postgres-$service pg_dump -U trading_admin -d $dbname -F c > "$BACKUP_DIR/${dbname}.backup"
    done
    
    # Create archive
    tar -czf "$BACKUP_DIR.tar.gz" -C backups "$(basename $BACKUP_DIR)"
    rm -rf "$BACKUP_DIR"
    
    log "Backup created: $BACKUP_DIR.tar.gz"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        log "Starting trading platform deployment..."
        check_requirements
        setup_directories
        start_services
        setup_database
        run_health_checks
        show_status
        log "Deployment completed successfully!"
        ;;
    "backup")
        create_backup
        ;;
    "stop")
        log "Stopping services..."
        docker-compose down
        log "Services stopped"
        ;;
    "restart")
        log "Restarting services..."
        docker-compose down
        docker-compose up -d
        run_health_checks
        log "Services restarted"
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose logs -f ${2:-}
        ;;
    *)
        echo "Usage: $0 {deploy|backup|stop|restart|status|logs [service]}"
        exit 1
        ;;
esac