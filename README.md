# saras-trading-platform
Saras multiuser trading platform

A scalable, Docker + Kubernetes based trading system using a single Zerodha admin account via Lean, with portfolio and smallcase management for multiple users.

---
```text
┌─────────────┐
│   Browser   │
│─────────────│
│ Svelte UI   │
│ TailwindCSS │
└─────┬───────┘
      │ HTTP (fetch / VITE_API_BASE_URL)
      ▼
┌──────────────┐
│  Web UI      │  <-- Docker container
│──────────────│
│ SvelteKit    │
│ Runs on 3000 │
└─────┬────────┘
      │ REST API call
      ▼
┌─────────────────┐
│ API Gateway     │  <-- Docker container
│─────────────────│
│ FastAPI (Python)│
│ Uvicorn (ASGI)  │
│ CORS Middleware │
│ Route: /portfolio/status │
└─────┬────────────┘
      │ Internal service call or DB access
      ▼
┌──────────────────┐
│ Portfolio Service│  (Optional Microservice Layer)
│──────────────────│
│ Python / FastAPI │
│ Portfolio logic  │
└─────┬────────────┘
      │ DB query
      ▼
┌────────────────────────────┐
│ PostgreSQL Database        │  <-- Docker container (planned)
│────────────────────────────│
│ Tables: Users, Holdings, etc. │
└────────────────────────────┘
```

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

On browser open - 127.0.0.1:8000/portfolio/status
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

### 12. Business Logic
How to execute the trade, splice it.
As there limitations on number of trades we can put in one go

### 13. Documentation
Videos and training material.


---

###  14. 🛠️ Full SvelteKit Frontend Development Setup Guide (Mac & Windows)

---

### ✅ 14.1. **Install Node.js (Correct Version)**

 Use **Node.js 20.19.x** or **22.12+**

#### Mac (recommended: via Homebrew + NVM)

```bash
# Install Homebrew if not done
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install NVM
brew install nvm

# Setup NVM directories
mkdir ~/.nvm
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.zshrc
echo '[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"' >> ~/.zshrc
source ~/.zshrc

# Install compatible Node version
nvm install 22
nvm use 22
```

#### Windows (via Node.js installer or NVM-Windows)

* Download [Node.js 22.x](https://nodejs.org/en/download)
* OR install [nvm-windows](https://github.com/coreybutler/nvm-windows) and run:

  ```bash
  nvm install 22
  nvm use 22
  ```

---

### ✅ 14.2. **Install SvelteKit App (Using `sv` instead of deprecated `create-svelte`)**

```bash
# Install the recommended `sv` package
npm install -g sv

# Create project folder
cd /your/dev/folder
sv create web-ui
cd web-ui
```

---

### ✅ 14.3. **Project Setup Options (Choose in CLI Prompt)**

* **Template**: SvelteKit + TypeScript + SSR
* **Adapter**: `adapter-auto`
* **Paraglide**: Yes (for multilingual support)
* **Prettier, ESLint**: Optional
* **Database support**: PostgreSQL
* **Package manager**: Choose `npm` or `pnpm` (we’ll use `npm` here)

---

### ✅ 14.4. **Install Dependencies**

```bash
npm install
```

---

### ✅ 14.5. **Fix Node Engine Compatibility (optional)**

If you see engine mismatch:

* Open `package.json` and change the `engines` field:

```json
"engines": {
  "node": ">=20.19"
}
```

---

### ✅ 14.6. **Run the App**

```bash
npm run dev -- --open
```

* This will open: [http://localhost:5173](http://localhost:5173)

---

### ✅ 14.7. **Set up `.env` (for PostgreSQL)**

Create a `.env` file in root:

```env
DATABASE_URL=postgres://your_user:your_password@localhost:5432/your_db
```

Avoid declaring `client = postgres()` multiple times.

---

### ✅ 14.8. **Connect to Backend (API Gateway)**

In your SvelteKit code, use `fetch` with your API Gateway base URL:

```ts
const res = await fetch('http://localhost:8000/trades', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});
```

---

### ✅ 14.9. **.gitignore**

Make sure to include:

```
node_modules/
.env
.vscode/
dist/
build/
.paraglide/
```

---

### ✅ 14.10. **Optional: Dockerize Later**

You can develop locally without Docker first, then containerize with:

```bash
npm run build
```

And use `Dockerfile` + `docker-compose.yml` to serve.


### ✅ 14.11 What to do instead (Tailwind v4 + SvelteKit)
Ensure the right packages are installed
npm i -D tailwindcss @tailwindcss/vite @tailwindcss/forms @tailwindcss/typography
Enable the Tailwind Vite plugin
Edit vite.config.ts (or vite.config.js):

import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwind from '@tailwindcss/vite';

export default defineConfig({
  plugins: [sveltekit(), tailwind()],
});
Import Tailwind in your global CSS
In src/app.css (create if missing):

@import "tailwindcss";

/* Optional plugins (forms, typography) */
@plugin "@tailwindcss/forms";
@plugin "@tailwindcss/typography";
Load the global CSS in your layout
In src/routes/+layout.svelte:

<script lang="ts">
  import '../app.css';
</script>

<slot />
Restart the dev server
npm run dev
Quick check
Add a test element somewhere (e.g., in +page.svelte):
<div class="p-4 bg-blue-600 text-white rounded">Tailwind v4 is working 🎉</div>
Notes
You can skip creating tailwind.config.* for now; Tailwind v4 works great with zero config.
If later you need deep customization (theme, content, etc.), you can add a config file manually (tailwind.config.ts/js) and Tailwind will pick it up.
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

