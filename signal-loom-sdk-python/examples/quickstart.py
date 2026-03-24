"""Quick-start example for the Signal Loom SDK.

Run with:  python examples/quickstart.py
"""

from signalloom import SignalLoom


def main() -> None:
    # Initialize the client. API key and base URL are read from environment
    # variables SIGNAL_LOOM_API_KEY and SIGNAL_LOOM_BASE_URL if not passed.
    client = SignalLoom()

    # ── Sync transcription (one call, blocks until ready) ─────────────────────
    #
    # Transcribe a remote URL:
    result = client.transcribe_sync(
        url="https://example.com/podcast.mp3",
    )

    # Print raw concatenated text
    print("=== Transcript ===")
    print(result.text)
    print()

    # Inspect structured segments
    print("=== Speakers ===")
    for segment in result.segments:
        print(f"[{segment.start:.1f}s - {segment.end:.1f}s] {segment.speaker}: {segment.text}")

    # Word-level timestamps
    if result.segments and result.segments[0].words:
        first_words = result.segments[0].words[:5]
        print("\n=== First 5 words ===")
        for w in first_words:
            print(f"  '{w.word}'  {w.start:.2f}s - {w.end:.2}s  (conf: {w.confidence:.2f})")

    # Summary (topics, entities, keywords)
    if result.summary:
        print("\n=== Summary ===")
        print(f"Topics:       {[t.topic for t in result.summary.topics]}")
        print(f"Keywords:     {result.summary.keywords}")
        print(f"Entities:     {[e.text for e in result.summary.entities]}")

    # Full JSON dump
    print("\n=== Full JSON ===")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
