# MLflow + Vertex AI LangChain POC

This POC demonstrates serving Vertex AI Gemini responses through FastAPI with two paths:
- **Direct SDK path** (`/vertex-text`): uses the Google `genai` client, pulls prompts from MLflow (if available), and returns structured JSON.
- **LangChain path** (`/vertex-text-langchain`): uses `ChatVertexAI` via LangChain, loads prompts from MLflow, and returns structured JSON.

Both paths fall back to default prompts when MLflow prompt artifacts are unreachable.

## Project layout
- `app/main.py` – FastAPI app exposing both endpoints.
- `app/vertex_resp.py` – direct Google Vertex AI SDK call; loads `prompts:/user_prompt@latest` and `prompts:/system_prompt@latest` from MLflow.
- `app/langchain_resp.py` – LangChain chain using `ChatVertexAI`, also loading prompts from MLflow and falling back to defaults.
- `local.yml` – Docker Compose for the app and an MLflow tracking server.
- `requirements.txt` – Python dependencies (FastAPI, LangChain, Vertex AI, MLflow, etc.).
- `Dockerfile` – container build for the app service.

## Prerequisites
- Google Cloud project and Vertex AI access; service account JSON mounted into the container and pointed by `GOOGLE_APPLICATION_CREDENTIALS`.
- Docker and Docker Compose.
- MLflow accessible at `MLFLOW_TRACKING_URI` (defaults to the compose service `http://mlflow:5000`).

## Running locally (compose)
From `poc_mlflow/`:

```
docker compose -f local.yml up --build
```

Services:
- App: `http://localhost:8000`
- MLflow UI: `http://localhost:5050`

Test calls:

```
curl -X POST http://localhost:8000/vertex-text \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain retrieval augmented generation"}'

curl -X POST http://localhost:8000/vertex-text-langchain \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize LangChain"}'
```

## Prompt loading via MLflow
- Prompts are stored in MLflow prompt artifacts and loaded with `mlflow.genai.load_prompt` using URIs `prompts:/user_prompt@latest` and `prompts:/system_prompt@latest`.
- If MLflow is unreachable, the code logs a warning and uses a simple default system prompt plus the raw user query.

## Deployment patterns for MLflow tracking server

### 1) All-in-one inside the tracking container (SQLite + local artifacts)
- **Backend store**: SQLite file inside the tracking container (e.g., `/mlflow/mlflow.db`).
- **Artifact store**: Local filesystem inside the same container (e.g., `/mlflow/artifacts`).
- **Pros**: Easiest to start; single container; no extra infra.
- **Cons**: Not durable for production; scaling/HA limited; data tightly coupled to container lifecycle unless the host mounts a volume.
- **Compose example**: the provided `local.yml` (binds `./mlflow_data` to `/mlflow`).

### 2) Split one component remote (artifact or DB) and keep the other local
- **Option A (common)**: DB stays local (SQLite/postgres in-container); artifact store remote (e.g., S3/GCS/Azure Blob). Set `--default-artifact-root s3://...` or `gs://...` and allow network egress. Good when artifacts are large and need durability.
- **Option B**: DB remote (managed Postgres/MySQL); artifacts local filesystem in-container. Set `--backend-store-uri postgresql://...` while keeping `--default-artifact-root /mlflow/artifacts`. This improves metadata durability but still couples artifact durability to the container volume.
- **Pros**: Incremental hardening; pick the durability pain point (metadata vs artifacts) to externalize first.
- **Cons**: Still a partial single point of failure; mixed durability story; more configs and secrets to manage.

### 3) Fully separated: tracking server, external DB, external artifact store
- **Backend store**: Managed Postgres/MySQL (e.g., Cloud SQL, RDS, Azure DB).
- **Artifact store**: Object storage bucket (GCS/S3/Blob) or NFS.
- **Tracking server**: Stateless service (container, VM, Kubernetes) pointing to the external DB and artifact root.
- **Pros**: Durable, scalable, stateless tracking server; easy to autoscale or restart; clearer backup/DR.
- **Cons**: More infra components; requires secure networking and secret management.

### Common flags and envs
- `--backend-store-uri`: SQLite path or SQLAlchemy URI (`postgresql://user:pass@host:port/db`).
- `--default-artifact-root`: Filesystem path or bucket URI (`s3://...`, `gs://...`).
- `MLFLOW_TRACKING_URI`: Point clients (app) to the tracking server (e.g., `http://mlflow:5000`).
- `MLFLOW_SERVE_ARTIFACTS=true`: Needed to serve artifacts over HTTP when using the built-in server.
- `--allowed-hosts "*" --cors-allowed-origins "*"`: Relaxed for POC; tighten for prod.

## Notes and hardening ideas
- Mount persistent volumes when using local SQLite/filesystem to avoid losing data on container rebuilds.
- For production, prefer pattern (3) with managed Postgres and bucket storage; front the tracking server with TLS and auth (reverse proxy or MLflow gateway options).
- Keep service account JSON outside the image; mount via secret/volume and reference with `GOOGLE_APPLICATION_CREDENTIALS`.
- Set tighter CORS/allowed-hosts and consider network policies when exposing MLflow beyond local dev.

## Quick troubleshooting
- MLflow unreachable: verify `MLFLOW_TRACKING_URI`, container health, and network/DNS (`mlflow` host in compose).
- Prompt not found: ensure `prompts:/user_prompt@latest` and `prompts:/system_prompt@latest` exist in MLflow; otherwise defaults are used.
- Vertex AI auth: confirm the service account has Vertex AI permissions and the JSON path is valid in the container.
- Long responses or failures: adjust `max_output_tokens`, `temperature`, and inspect container logs (`docker compose logs app mlflow`).
