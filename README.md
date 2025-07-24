# saras-trading-platform
Saras multiuser trading platform

A scalable, Docker + Kubernetes based trading system using a single Zerodha admin account via Lean, with portfolio and smallcase management for multiple users.

---

## 🧩 Components Overview

### 1. `api-gateway/`
**Function:** Routes requests to backend services, applies authentication and rate limiting  
**Stack:** FastAPI / NGINX / Kong / Traefik  
**Input:** HTTP API requests from clients  
**Output:** Routes to microservices; returns service responses  


### 1.1 Build the Docker Image
Navigate into the api-gateway/ folder and run:
docker build -t api-gateway:latest .


### 1.2. Run the Container
docker run -d -p 8000:8000 api-gateway:latest

---

### 2. `user-service/`
**Function:** Handles user registration, login, JWT authentication, KYC info  
**Stack:** FastAPI, PostgreSQL, SQLAlchemy  
**Input:** `POST /register`, `POST /login`, `GET /me`  
**Output:** Auth tokens, user profile, success/failure responses  

---

### 3. `portfolio-service/`
**Function:** Manages user portfolios and holdings  
**Stack:** FastAPI, PostgreSQL, Redis (cache), Alembic (migrations)  
**Input:** `GET /portfolio`, `POST /portfolio`, `POST /buy`, `POST /sell`  
**Output:** Portfolio details, transaction logs, error/success messages  

---

### 4. `smallcase-service/`
**Function:** Allows users to create, modify, and track smallcases (bundles of stocks)  
**Stack:** FastAPI, PostgreSQL  
**Input:** `POST /smallcase`, `PUT /smallcase/:id`, `GET /smallcase/:id`  
**Output:** Smallcase composition, expected returns, validation status  

---

### 5. `trade-executor/`
**Function:** Consumes trade requests, consolidates them, and sends to Zerodha via Lean Engine using admin account  
**Stack:** Python, Zerodha API, Lean Engine, Celery, RabbitMQ  
**Input:** Trade jobs from queue  
**Output:** Execution confirmation, transaction stored in DB  

---

### 6. `notification-service/`
**Function:** Sends push/email/SMS notifications for trades, alerts, reports  
**Stack:** FastAPI, Celery, SMTP/Twilio API  
**Input:** Notification task (from other services)  
**Output:** Delivery status  

---

### 7. `analytics-service/`
**Function:** Provides historical data, performance analytics, reports  
**Stack:** FastAPI, Pandas, PostgreSQL, Plotly  
**Input:** `GET /analytics?user_id=xxx`  
**Output:** JSON or graphs/charts on returns, volatility, etc  

---

### 8. `common/`
**Function:** Shared utility modules  
- `auth/`: JWT encode/decode, permissions  
- `database/`: ORM session, migrations  
- `utils/`: Common helpers (logging, retry, caching)

---

### 9. `infra/`
Infrastructure services (run in Docker containers or Kubernetes):
- `postgres/` - User/portfolio DB
- `redis/` - Cache
- `rabbitmq/` - Message queue for executor & notification
- `prometheus-grafana/` - Monitoring and visualization

---

### 10. `scripts/`
Utility scripts:
- DB seeding
- Admin trade trigger manual
- Backup and restore

---

### 11. `k8s/`
Kubernetes deployment manifests:
- Deployments for each service
- LoadBalancer/Ingress YAMLs
- Horizontal Pod Autoscalers
- ConfigMaps for environment vars

---

## 🚀 How It Works (Data Flow)

1. User logs in → receives JWT token.
2. Submits a trade via `portfolio-service` or `smallcase-service`.
3. Trade request pushed to RabbitMQ queue.
4. `trade-executor` aggregates requests and calls Zerodha API via Lean.
5. Response stored in DB, and triggers `notification-service`.

---

## 🛠️ Tech Stack Summary

| Layer                | Tech                                  |
|---------------------|----------------------------------------|
| API Gateway         | Traefik / Kong / NGINX                 |
| Microservices       | Python (FastAPI), Docker, Celery       |
| Broker API          | Zerodha Kite API via Lean Engine       |
| DB / Cache / Queue  | PostgreSQL, Redis, RabbitMQ            |
| Monitoring          | Prometheus + Grafana, ELK/Loki         |
| Orchestration       | Kubernetes (k8s), Helm                 |
| Messaging           | RabbitMQ (trade, alert, background job)|
| Auth                | JWT-based                              |

---

## 📦 Future Enhancements

- AI-based smallcase suggestions
- Role-based dashboards (admin vs user)
- Real-time updates via WebSockets
- Multi-admin failover support

---

## 👨‍💻 Contributions

- Microservice APIs follow REST principles
- Each service includes Dockerfile + health checks
- Deployable individually or as a full stack using `docker-compose` or `Helm`

