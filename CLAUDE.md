# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
# Start all services (creates .env from template if missing)
./start.sh

# Manual startup
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v
```

### Service Access
- **Web UI**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: trading_user, db: trading_dev)
- **PgBouncer**: localhost:6432
- **Redis**: localhost:6379
- **RabbitMQ Management**: http://localhost:15672 (user: trading_user, pass: dev_password_123)
- **PgAdmin**: http://localhost:8080 (admin@trading.com / admin123)

### Python Services
- **API Gateway**: FastAPI service running on port 8000
- **Requirements**: Each service has its own requirements.txt
- **Virtual Environment**: Services use containerized environments
- **Database**: Uses SQLAlchemy with AsyncPG for PostgreSQL

### Frontend Development
- **React/Next.js UI**: Located in `web-ui/` directory
- **Commands**: `npm run dev`, `npm run build`, `npm run check`
- **Type Checking**: TypeScript with `tsc` checking
- **Database**: Uses Drizzle ORM with `npm run db:push`
- **Styling**: Tailwind CSS with Radix UI components

## Architecture Overview

### Microservices Structure
The platform follows a microservices architecture with these core services:

- **API Gateway** (`api-gateway/`): Main entry point, routing, authentication middleware
- **User Service** (`user-service/`): User registration, login, JWT authentication, KYC
- **Portfolio Service** (`portfolio-service/`): Portfolio management, holdings, transactions
- **Smallcase Service** (`smallcase-service/`): Smallcase creation, modification, tracking
- **Trade Executor** (`trade-executor/`): Trade execution via broker APIs (Zerodha, Alpaca)
- **Notification Service** (`notification-service/`): Push/email/SMS notifications
- **Analytics Service** (`analytics-service/`): Performance analytics, historical data

### Key Components
- **Common** (`common/`): Shared utilities, auth helpers, database utilities
- **Database** (`database/`): PostgreSQL schemas, migrations, initialization scripts
- **Infrastructure** (`infra/`): Docker configurations for supporting services
- **Kubernetes** (`k8s/`): Deployment manifests for production
- **Scripts** (`scripts/`): Database seeding, setup utilities, admin tools

### Service Communication
- **Message Queue**: RabbitMQ for asynchronous trade execution and notifications
- **Caching**: Redis for session management and performance optimization
- **Database**: PostgreSQL with PgBouncer connection pooling
- **API**: REST APIs with FastAPI, JWT authentication
- **WebSockets**: Real-time updates for portfolio and trade status

### Authentication & Security
- **JWT Tokens**: Managed in API Gateway with auth middleware
- **Environment Variables**: Broker API keys, database credentials via .env
- **CORS**: Configured for frontend origins (localhost:3000)
- **Security Logging**: Dedicated security event logging in API Gateway

## Development Environment

### Required Environment Variables
Create `.env` file with:
```bash
JWT_SECRET_KEY=your-secret-key-here
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ZERODHA_API_KEY=your-zerodha-key
ZERODHA_SECRET_KEY=your-zerodha-secret
```

### Service Dependencies
Services must start in order due to dependencies:
1. PostgreSQL (with health checks)
2. PgBouncer, Redis, RabbitMQ
3. API Gateway (depends on all infrastructure)
4. Web UI (depends on API Gateway)

### Database Management
- **Initialization**: SQL scripts in `database/init/`
- **Connection Pooling**: PgBouncer configured with transaction-level pooling
- **Backup Location**: `database/backups/`
- **Test Data**: Scripts available in `scripts/` directory

## Broker Integration

### Supported Brokers
- **Zerodha**: Primary broker integration via Kite API
- **Alpaca**: Secondary broker for US markets
- **Lean Engine**: Trade execution framework

### Trade Flow
1. User submits trade via portfolio or smallcase service
2. Trade request queued in RabbitMQ
3. Trade executor aggregates and consolidates requests
4. Execution via broker API using admin account
5. Results stored in database, notifications triggered

## Testing & Quality

- **No formal test framework detected**: Consider adding pytest for Python services and Jest/Vitest for frontend
- **Linting**: No specific linting commands found in package.json
- **Type Checking**: TypeScript checking available via `npm run check` for frontend

## Production Deployment

- **Kubernetes**: Manifests available in `k8s/` directory
- **Production Plan**: Detailed roadmap in `PRODUCTION.PLAN.md`
- **Docker**: Production-ready Dockerfiles for each service
- **Monitoring**: Planned integration with Prometheus/Grafana (see production plan)