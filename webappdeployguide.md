# Web App Deploy Guide (GCP)

This guide covers **theory + practice** to deploy the BoardGamePy web app on Google Cloud Platform. It explains the architecture choices, how frontend and backend communicate, and includes both **gcloud CLI** steps and **GCP Console (UI)** steps.

Contents:
1. Architecture Overview
2. Data Persistence: Cloud SQL vs BigQuery
3. Recommended Deployment Option
4. Environment Variables and Cross‑Service Communication
5. Deploying the Backend (Cloud Run)
6. Deploying the Frontend (Cloud Storage + CDN)
7. Rate Limiting + DDoS Protection (Cloud Armor)
8. Troubleshooting Checklist
9. One‑Command Deploy Script

---

## 1. Architecture Overview

You have a **frontend** (Vite/React) and a **backend** (FastAPI + SQLModel + SQLite by default).

**Key concepts:**
- **Frontend** is static assets (HTML/CSS/JS). It calls the backend API via HTTP.
- **Backend** serves API endpoints and manages game sessions.
For production you should **separate** them:
- Frontend: static hosting (Cloud Storage + CDN)
  - Backend: Cloud Run
- You must configure the frontend to point at the backend URL using `VITE_API_URL`.

---

## 2. Data Persistence: Cloud SQL vs BigQuery

For **persistent app data**, use **Cloud SQL (Postgres)**.  
BigQuery is for analytics, not for transactional app state.

**Use Cloud SQL if you need:**
- Persistent sessions, logs, rate‑limit tracking
- Low‑latency reads/writes

**Do not use BigQuery for this app.**

---

## 3. Recommended Deployment Option

- **Backend** on **Cloud Run**
- **Frontend** on **Cloud Run** (dev server style)

Pros: identical to local `npm run dev` behavior.  
Cons: not optimal for production, higher cost, slower.

---

## 4. Env Vars and Communication

Frontend needs to call backend:

```
VITE_API_URL=https://YOUR_BACKEND_URL
```

Backend should allow frontend origin in CORS:

```
FRONTEND_ORIGINS=https://YOUR_FRONTEND_URL
```

Other backend envs you already use:

```
OPENROUTER_API_KEY=... (required only if you want AI players)
DATABASE_URL=sqlite+aiosqlite:///./webapp.db
```

**Important:**
- Cloud Run container filesystem is **ephemeral**. SQLite will reset on new deployments.
- If you want persistent data, use **Cloud SQL** instead of SQLite.
- If `OPENROUTER_API_KEY` is not set, the backend can still start, but AI seats will fail. For production, set the key or only allow human seats.

If using Cloud SQL (Postgres), set:
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@/DB?host=/cloudsql/INSTANCE_CONNECTION_NAME
```

---

## 5. Deploying the Backend (Cloud Run)

### Build a container
We’ll use Docker. Add a Dockerfile if you don’t have one.

Create `webapp/backend/Dockerfile`:

```
FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY src /app/src
COPY examples /app/examples
COPY webapp /app/webapp

RUN pip install uv && uv pip install --system -e .

EXPOSE 8000
CMD ["uvicorn", "webapp.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### gcloud CLI steps

```
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry
gcloud artifacts repositories create bgpy-repo \
  --repository-format=docker --location=us-central1

# Build and push
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/bgpy-repo/bgpy-backend \
  .

# Deploy to Cloud Run
gcloud run deploy bgpy-backend \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/bgpy-repo/bgpy-backend \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=YOUR_KEY,FRONTEND_ORIGINS=https://YOUR_FRONTEND_URL
```

Cloud Run outputs a URL like:
```
https://bgpy-backend-xxxxxxxx-uc.a.run.app
```

### GCP Console steps (UI)
1. Go to **Cloud Run**
2. Click **Create Service**
3. Choose **Deploy one revision from existing container image**
4. Select the image from Artifact Registry
5. Allow unauthenticated access
6. Under **Variables & Secrets**, set:
   - `OPENROUTER_API_KEY`
   - `FRONTEND_ORIGINS`
7. Click **Create**

---

## 6. Deploying the Frontend (Cloud Run, dev server style)

Create `webapp/frontend/Dockerfile` (already in repo):

```
FROM node:20-slim
WORKDIR /app
COPY webapp/frontend/package*.json /app/
RUN npm install
COPY webapp/frontend /app
EXPOSE 8080
CMD ["sh", "-c", "VITE_API_URL=${VITE_API_URL} npm run dev -- --host 0.0.0.0 --port ${PORT:-8080}"]
```

Build + deploy:

```
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/bgpy-repo/bgpy-frontend \
  webapp/frontend

gcloud run deploy bgpy-frontend \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/bgpy-repo/bgpy-frontend \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://YOUR_BACKEND_URL
```

---

## 7. Rate Limiting + DDoS Protection

You already have **app‑level rate limits** (30 sessions/hour/IP). For DDoS protection:

### Cloud Armor (recommended)
1. Create a **HTTP(S) Load Balancer**
2. Attach your Cloud Run service via **Serverless NEG**
3. Add a **Cloud Armor policy**:
   - Rate‑based rule: e.g. `1000 req/min/IP`
   - Optional: Geo/IP reputation blocking

### Quick UI steps
1. Go to **Network Services → Cloud Armor**
2. Create policy
3. Add rules (rate limiting + allowlist/denylist)
4. Attach policy to the Load Balancer backend

---

## 8. Troubleshooting

**Frontend can’t reach backend**
- Check `VITE_API_URL` in build
- Check backend CORS `FRONTEND_ORIGINS`

**Backend errors with SQLite**
- Cloud Run is ephemeral; use Cloud SQL for persistence.

**Rate limit errors**
- Expected after 30 sessions/hour/IP; frontend shows reset time.

---

## Optional: Single Domain Routing

You can use a single domain by hosting frontend and backend under one HTTPS Load Balancer:
- `/` → frontend bucket or Cloud Run
- `/api/*` → backend Cloud Run

This avoids CORS and makes the app feel “single origin”.

---

If you want, I can:
- Generate Dockerfiles automatically based on your repo.
- Add Cloud SQL migrations for persistence.
- Add Terraform so this is repeatable.  

---

## 9. One‑Command Deploy Script

There is now a script at:

```
scripts/deploy_gcp.sh
```

It deploys:
- Backend → Cloud Run
- Frontend → Cloud Run (dev server)
- Cloud SQL Postgres (persistent storage)

### Required environment variables

```
PROJECT_ID=your-gcp-project
DB_PASSWORD=your-db-password
OPENROUTER_API_KEY=your-openrouter-key   # optional if you only use human seats
```

### Optional overrides

```
REGION=us-central1
REPO_NAME=bgpy-repo
BACKEND_SERVICE=bgpy-backend
FRONTEND_SERVICE=bgpy-frontend
DB_INSTANCE=bgpy-sql
DB_NAME=bgpy
DB_USER=bgpy
```

### Run it

```
chmod +x scripts/deploy_gcp.sh
./scripts/deploy_gcp.sh
```

The script will print the final backend and frontend URLs.
