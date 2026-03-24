"""Async workflow example for the Signal Loom SDK.

Demonstrates submitting a job and polling for status manually.
"""

from signalloom import SignalLoom


def main() -> None:
    client = SignalLoom()

    # ── Async: submit and poll ─────────────────────────────────────────────────

    # Submit with a local file
    with open("audio.mp3", "rb") as fh:
        job = client.transcribe(
            file=fh,
            model="mlx-community/whisper-large-v3-turbo",
            language="en",
            word_timestamps=True,
        )

    print(f"Job submitted: {job.job_id}  (status: {job.status})")

    # Manually poll until done
    while job.status not in ("completed", "failed", "cancelled"):
        import time
        time.sleep(2)
        job = client.get_job(job.job_id)
        print(f"  status: {job.status}  progress: {job.progress}")

    if job.status == "completed":
        result = client.get_result(job.job_id)
        print(f"\nTranscript ({result.duration_seconds:.1f}s):")
        print(result.text)
    else:
        print(f"\nJob ended with status: {job.status}  error: {job.error}")

    # ── LangChain tool example ─────────────────────────────────────────────────
    #
    # from langchain.tools import StructuredTool
    #
    # def transcribe_audio(audio_url: str) -> str:
    #     result = SignalLoom().transcribe_sync(url=audio_url)
    #     return result.model_dump_json(indent=2)
    #
    # tool = StructuredTool.from_function(
    #     transcribe_audio,
    #     name="transcribe_audio",
    #     description="Transcribe an audio or video file URL to structured JSON",
    # )


if __name__ == "__main__":
    main()
