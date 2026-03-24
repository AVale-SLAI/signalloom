# Signal Loom AI — Models Router
"""
GET /v1/models — List available transcription models
GET /v1/models/{model} — Get details about a specific model
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core import DEFAULT_MODEL, SUPPORTED_MODELS

router = APIRouter()

MODEL_DESCRIPTIONS = {
    "mlx-community/whisper-large-v3-turbo": {
        "id": "mlx-community/whisper-large-v3-turbo",
        "name": "Whisper Large V3 Turbo",
        "provider": "mlx (Apple Silicon)",
        "type": "speech-to-text",
        "multilingual": True,
        "languages": "99+",
        " speed": "fast (Turbo)",
        "recommended": True,
        "notes": "Best balance of speed and quality for Apple Silicon. Recommended default.",
    },
    "mlx-community/whisper-large-v3": {
        "id": "mlx-community/whisper-large-v3",
        "name": "Whisper Large V3",
        "provider": "mlx (Apple Silicon)",
        "type": "speech-to-text",
        "multilingual": True,
        "languages": "99+",
        "speed": "slower",
        "recommended": False,
        "notes": "Larger model, higher accuracy but slower than Turbo.",
    },
    "openai/whisper-large-v3": {
        "id": "openai/whisper-large-v3",
        "name": "Whisper Large V3 (OpenAI)",
        "provider": "OpenAI API",
        "type": "speech-to-text",
        "multilingual": True,
        "languages": "99+",
        "speed": "depends on API",
        "recommended": False,
        "notes": "Requires OpenAI Whisper API key and incurs per-minute costs.",
    },
}


@router.get("/models")
def list_models():
    """
    List all available transcription models.

    Returns model ID, provider, language support, and recommended flag.
    """
    models = []
    for model_id in SUPPORTED_MODELS:
        desc = MODEL_DESCRIPTIONS.get(model_id, {
            "id": model_id,
            "name": model_id,
            "provider": "unknown",
            "type": "speech-to-text",
            "multilingual": True,
            "recommended": model_id == DEFAULT_MODEL,
            "notes": "Available but not locally described.",
        })
        models.append(desc)

    return {
        "models": models,
        "default": DEFAULT_MODEL,
        "count": len(models),
    }


@router.get("/models/{model_id}")
def get_model(model_id: str):
    """Get details about a specific model."""
    if model_id not in SUPPORTED_MODELS:
        raise HTTPException(status_code=404, detail=f"Model not available: {model_id}")

    desc = MODEL_DESCRIPTIONS.get(model_id, {
        "id": model_id,
        "name": model_id,
        "recommended": model_id == DEFAULT_MODEL,
    })
    return desc
