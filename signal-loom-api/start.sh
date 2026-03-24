#!/bin/bash
# Signal Loom AI API launcher
# Ensures signal-loom-api packages take priority over workspace packages

cd /Users/aehs-mini-ctrl/.openclaw/workspace/signal-loom-api
export PYTHONPATH="/Users/aehs-mini-ctrl/.openclaw/workspace/signal-loom-api:/Users/aehs-mini-ctrl/.openclaw/workspace"
exec /usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 18790
