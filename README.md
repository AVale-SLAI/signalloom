# Signal Loom AI

**Media In. Machine Intelligence Out.**

Structured transcription API — converts audio and video into agent-readable knowledge objects.

```
pip install signalloom
```

```python
from signalloom import SignalLoom
client = SignalLoom(api_key="slo_...")
result = client.transcribe_sync(file="podcast.mp3")
# Returns: structured JSON with entities, topics, timestamps, summary
```

## Repositories

| Project | Description |
|---------|-------------|
| [signal-loom-api](./signal-loom-api) | FastAPI transcription server |
| [signal-loom-sdk-python](./signal-loom-sdk-python) | Python SDK (`pip install signalloom`) |
| [signal-loom-landing](./signal-loom-landing) | Landing page |
| [signal-loom-strategy](./signal-loom-strategy) | Business plans, roadmaps, strategy |

## Quick Start

```bash
# API server
cd signal-loom-api
pip install -r requirements.txt
python -m uvicorn main:app --port 18790

# Python SDK
cd signal-loom-sdk-python
pip install .
```

## Links

- 🌐 **API Docs:** [api.signalloomai.com/docs](https://api.signalloomai.com/docs)
- 📄 **Landing:** [signalloomai.com](https://signalloomai.com)
- 📦 **PyPI:** [pypi.org/project/signalloom](https://pypi.org/project/signalloom)
