# Signal Loom AI — API Service

**Version:** 0.1.0-alpha

FastAPI service that exposes the Signal Loom transcription pipeline as a REST API.

## Quick Start

```bash
# Install dependencies
cd signal-loom-api
pip install fastapi uvicorn python-multipart pydantic-settings httpx

# Run locally
uvicorn main:app --reload --port 18790 --host 0.0.0.0

# Test
curl http://localhost:18790/health
```

## API Docs

Once running:
- Swagger UI: <http://localhost:18790/docs>
- ReDoc: <http://localhost:18790/redoc>

## Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/transcribe/sync` | **One-call sync transcription** — submit and get result in one request |
| `POST` | `/v1/transcribe` | Submit a transcription job (file upload or URL) |
| `GET` | `/v1/status/{job_id}` | Check job status |
| `GET` | `/v1/result/{job_id}` | Get transcript result |
| `GET` | `/v1/jobs` | List all jobs |
| `DELETE` | `/v1/job/{job_id}` | Delete a job |
| `GET` | `/v1/download/{job_id}` | Download transcript in json/txt/srt/vtt |
| `GET` | `/v1/models` | List available transcription models |
| `GET` | `/health` | Full health check |


## Output Schema

The API returns **structured, machine-readable JSON** — not raw transcript text. Every response includes typed segments with speakers, topics, entities, and sentiment.

See **[API_SCHEMA.md](../signal-loom/API_SCHEMA.md)** for the full schema reference, including segment structure, entity types, sentiment format, and code examples for LangChain and LlamaIndex.

## Compatibility

See **[COMPATIBILITY.md](../signal-loom/COMPATIBILITY.md)** for supported file formats, language support, Whisper model compatibility, and known limitations.

## Authentication

MVP: open (no auth required).  
Production: set `SIGNAL_LOOM_REQUIRE_API_KEY=true` and provide `SIGNAL_LOOM_VALID_API_KEYS`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGNAL_LOOM_DEFAULT_MODEL` | `mlx-community/whisper-large-v3-turbo` | Default transcription model |
| `SIGNAL_LOOM_MAX_CONCURRENT_JOBS` | `2` | Max parallel transcription jobs |
| `SIGNAL_LOOM_REQUIRE_API_KEY` | `false` | Require API key authentication |
| `SIGNAL_LOOM_HOST` | `0.0.0.0` | Server bind host |
| `SIGNAL_LOOM_PORT` | `18790` | Server bind port |
| `SIGNAL_LOOM_DEBUG` | `false` | Enable debug mode |
| `OLLAMA_ENDPOINT` | _(none)_ | Optional Ollama endpoint for embedding/normalization |

## Production Deployment

```bash
# Railway / Render / Fly.io
pip install fastapi uvicorn python-multipart pydantic-settings httpx gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:18790
```

## Architecture

```
signal-loom-api/
  main.py              # FastAPI app + lifespan
  core/                # Configuration and environment
  routers/
    transcribe.py      # Transcription endpoints
    health.py          # Health/readiness endpoints
    models.py          # Model listing
  jobs/
    __init__.py        # JobManager (in-memory, swap for Redis/Postgres in prod)
  schemas/
    __init__.py        # Pydantic request/response models
```

## Status Codes

| Status | Meaning |
|--------|---------|
| `queued` | Job received, waiting for worker |
| `processing` | Transcription in progress |
| `completed` | Done — GET /result/{job_id} |
| `failed` | Error — check `error` field |

## Output Formats

- `json` — Full Signal Loom knowledge object with segments, metadata, timestamps
- `txt` — Plain text transcript
- `srt` — Subtitle format with timestamps
- `vtt` — WebVTT subtitle format
