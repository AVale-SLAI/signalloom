# Signal Loom Python SDK

> Python client library for the Signal Loom AI media-to-agent ingestion API.

`signal-loom-sdk-python` provides a clean Python interface to the Signal Loom API,
which transcribes audio and video into structured, machine-readable JSON — not raw
text. Speaker diarization, entity extraction, topic classification, sentiment
analysis, and word-level timestamps are all included in the standard response.

## Features

- **Sync & async transcription** — one-call blocking (`transcribe_sync`) or
  job-based async (`transcribe` + polling)
- **Structured output** — Pydantic models for segments, words, speakers,
  entities, topics, sentiment, and summary
- **Multipart file uploads** — pass a file path, file handle, or bytes
- **Exponential back-off polling** — built into `transcribe_sync`
- **Context manager** — `with SignalLoom() as client:` for automatic cleanup
- **LangChain integration** — drop-in tool for agent pipelines

## Installation

```bash
pip install signalloom
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add signalloom
```

### Optional dependencies

```bash
# Development tools
pip install signalloom[dev]

# LangChain integration
pip install signalloom[langchain]
```

## Quick Start

```python
from signalloom import SignalLoom

client = SignalLoom()

# One-call synchronous transcription
result = client.transcribe_sync(url="https://example.com/podcast.mp3")

print(result.text)                    # raw concatenated text
print(result.segments[0].speaker)     # "SPEAKER_1"
print(result.summary.keywords)        # ["keyword1", "keyword2"]
print(result.model_dump_json(indent=2))  # full structured JSON
```

## Async workflow

```python
from signalloom import SignalLoom

client = SignalLoom()

job = client.transcribe(file=open("audio.mp3", "rb"))
print(f"Job ID: {job.job_id}")

# Poll manually
import time
while job.status not in ("completed", "failed", "cancelled"):
    time.sleep(2)
    job = client.get_job(job.job_id)

result = client.get_result(job.job_id)
print(result.text)
```

## Configuration

| Environment variable | Parameter | Default |
|---------------------|-----------|---------|
| `SIGNAL_LOOM_API_KEY` | `api_key` | `None` |
| `SIGNAL_LOOM_BASE_URL` | `base_url` | `http://localhost:18790` |

```python
# All three are equivalent:
client = SignalLoom()
client = SignalLoom(base_url="http://localhost:18790")
client = SignalLoom(api_key="sk-...", base_url="https://api.signalloom.ai")
```

## API Reference

### `SignalLoom`

```python
SignalLoom(api_key=None, base_url=None, timeout=300)
```

#### Methods

- **`transcribe(file=None, url=None, **kwargs) -> Job`**  
  Submit an async transcription job. Exactly one of `file` or `url` is required.

- **`transcribe_sync(file=None, url=None, timeout=None, **kwargs) -> Transcript`**  
  One-call blocking transcription. Polls internally with exponential back-off.

- **`get_job(job_id: str) -> Job`**  
  Fetch current job status.

- **`get_result(job_id: str) -> Transcript`**  
  Fetch completed transcript.

- **`cancel_job(job_id: str) -> bool`**  
  Cancel a queued or running job.

- **`list_jobs(status=None) -> List[Job]`**  
  List all jobs, optionally filtered by status string.

#### Properties

- **`health -> dict`** — Server health info (`GET /health`)
- **`info -> ServerInfo`** — Server capabilities and model list (`GET /v1/info`)
- **`models -> List[str]`** — Available model IDs

### Transcript model

```python
result.text                    # str — concatenated segment texts
result.segments                # List[TranscriptSegment]
result.segments[0].speaker     # str — "SPEAKER_1"
result.segments[0].words       # List[Word] — word-level timestamps
result.segments[0].entities    # List[Entity] — extracted entities
result.segments[0].sentiment   # Sentiment — label + score
result.summary.topics          # List[Topic]
result.summary.keywords        # List[str]
result.metadata.audio_duration # float — seconds
```

## LangChain integration

```python
from langchain.tools import StructuredTool
from signalloom import SignalLoom

def transcribe_tool(audio_url: str) -> str:
    result = SignalLoom().transcribe_sync(url=audio_url)
    return result.model_dump_json(indent=2)

tool = StructuredTool.from_function(
    transcribe_tool,
    name="transcribe_audio",
    description="Transcribe an audio or video URL to structured JSON",
)
```

## Error handling

| Exception | HTTP status |
|-----------|-------------|
| `SignalLoomError` | any error |
| `InvalidRequestError` | 400 |
| `RateLimitError` | 429 |
| `JobFailedError` | job failed |
| `TimeoutError` | sync timeout |

```python
from signalloom import SignalLoom, TimeoutError, JobFailedError

client = SignalLoom()
try:
    result = client.transcribe_sync(url="https://example.com/audio.mp3", timeout=60)
except TimeoutError:
    print("Job took too long")
except JobFailedError as e:
    print(f"Job failed: {e.job_id}")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check signalloom/

# Type check
mypy signalloom/
```

## License

MIT License — see [LICENSE](LICENSE).
