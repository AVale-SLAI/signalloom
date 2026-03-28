# Signal Loom AI — Explainer Video Brief
**For: Marketing Firm / Video Production Team**
**Prepared by: Aster Vale (Chief of Staff, Signal Loom AI)**
**Date: 2026-03-28**
**Version: 1.0 — Internal Draft**

---

## What Signal Loom AI Does (One Sentence)

Signal Loom AI turns audio and video — YouTube videos, uploaded recordings, live streams — into structured, timestamped, machine-readable JSON that AI systems can actually use, not just raw transcript text.

---

## The Problem We Solve

**The world is full of audio and video that AI systems can't access.**

- Meeting recordings pile up. Transcripts are unsearchable black holes.
- AI can't cite evidence from audio. It can say "the recording mentioned X" but can't point to when.
- Every team building AI features has built (or is building) their own Whisper pipeline: ffmpeg normalization, timestamp alignment, speaker diarization. That's weeks of work before they ship one useful feature.
- OpenAI changes their Whisper output format → your parsing breaks → your product breaks.

**The structural understanding layer is missing from the AI stack.**

---

## The Product

**API-first.** Developers integrate in minutes. No GUI required for core use.

**Three ways to use it:**
1. YouTube URL → structured JSON (the live demo anyone can try)
2. File upload → structured JSON (mp3, mp4, m4a, wav, etc.)
3. Real-time WebSocket streaming → partial timestamped transcripts as audio happens

**The output is not a transcript. It's a knowledge object:**
```json
{
  "schema": "Signal Loom Schema v1",
  "source_ref": "youtube.com/watch?v=dQw4w9WgXcQ",
  "duration_seconds": 213.04,
  "language": "en",
  "segments": [
    {
      "segment_id": "S1",
      "start_seconds": 0.0,
      "end_seconds": 21.88,
      "text": "We're no strangers to love..."
    }
  ],
  "metadata": {
    "ffprobe": { "media_kind": "audio", "duration_seconds": 213.04 }
  }
}
```

**vs. what you'd get from raw Whisper:**
```
"We're no strangers to love. You know the rules and so do I..."
```
No timestamps. No provenance. No structure. No citations.

---

## Who The Video Is For

**Primary audience: AI product engineers and technical decision-makers**
- CTOs building AI features
- Staff engineers evaluating infrastructure
- AI product leads choosing speech/navigation APIs
- Founders building agents, retrieval systems, voice features

**Secondary audience: technical managers evaluating tools for their team**
- VPs of Engineering
- Heads of AI Platform
- Technical co-founders

**What they need to understand after watching:**
1. What the structural intelligence layer is and why it matters
2. That the product works — demonstrated live
3. How to get started (API key in 60 seconds, free tier)
4. Why Signal Loom specifically — what's the differentiation

---

## Key Messages (Do Not Lose These)

**Brand position:** "The structural understanding layer for AI — not just a transcript."

**Core value proposition:** "Stop building Whisper pipelines. Start shipping AI features."

**GTM anchor:** Sell the layer. Acquire through the symptom. Convert through proof.

**Differentiation:** Not a speech-to-text engine. A structured intelligence infrastructure layer. We use best-in-class STT underneath — the product is the schema, not the transcription.

**The one-liner for engineers:** "Get timestamps, speaker labels, and entity tags from any audio or video — not just text."

---

## The Structure We Recommend

### Opening (0:00–0:20)
**Hook:** The cost of unstructured audio.
- Show: a pile of meeting recordings, a video archive, a podcast library — all inaccessible to AI.
- Voice: "You're recording everything. You're using almost none of it."
- Cut to: AI answering a question about a meeting with no citation, hallucinating context.
- Voice: "This is what happens when AI has no structure to work with."

### The Transformation (0:20–1:00)
**Show what Signal Loom does to the problem.**
- Show: a YouTube URL pasted into the demo. 30 seconds later: structured JSON.
- Highlight: timestamps, segment IDs, source reference, language, duration.
- Voice: "One URL. 30 seconds. A knowledge object — not a transcript."
- Show: the same JSON used as a RAG citation — AI answers with a timestamp and segment reference.
- Voice: "Now your AI can say 'at 4 minutes and 23 seconds, the speaker said X' — and mean it."

### The Three Ways to Use It (1:00–1:45)
**Quick visual breakdown of the three modes:**
1. **YouTube → JSON** (show the demo page live)
2. **File Upload → JSON** (show the API, show the JSON output)
3. **Real-Time WebSocket** (show partial results updating — "done: false" → "done: true")

### Why Signal Loom (1:45–2:15)
**Differentiation — be specific:**
- "Other services give you text. We give you structure — timestamps, speakers, provenance."
- "We maintain the schema contract. When Whisper changes its output, we update under you. Your pipeline doesn't break."
- "The free tier is real — 100 minutes, no credit card, API key in 60 seconds."
- Show: pricing tiers briefly. Starter $25, Pro $99, Scale $349.
- "Scale as your product grows. Cancel anytime."

### Demo Moment (2:15–2:45)
**The strongest conversion tool we have:**
- Live demo: paste a YouTube URL of a real video (something the viewer recognizes — a podcast, talk, or interview).
- Watch it process.
- Show the JSON appear.
- Voice over: "This is what your AI pipeline has been missing."

### Call to Action (2:45–3:00)
- "Start free. 100 minutes a month, no credit card."
- "API key in 60 seconds at signalloomai.com"
- Show: the signup flow in 10 seconds (email → API key → first transcription)
- Close on the logo + tagline: "Signal Loom — the structural understanding layer for AI."

---

## Visual Style Guidance

**Overall feel:** Technical credibility meets clean minimalism. Not flashy. Not corporate blue. The aesthetic of a well-built developer tool — dark theme, precise, confident.

**Color:** Dark background (#0a0a0f). Accent: electric blue (#5B8DF9). White text. Think VS Code meets Linear.

**Motion:** Smooth, fast transitions. No swooping. No particle effects. Think: the precision of a terminal, the polish of a modern SaaS product.

**Typography:** System monospace for code/technical content. Clean sans-serif for narration. SF Mono, Fira Code, or similar.

**What NOT to do:**
- Don't use generic AI stock footage (robots, glowing brains, data streams)
- Don't use corporate blue gradients
- Don't explain what Whisper is — our buyers already know
- Don't use "game-changing" or "revolutionary" language
- Don't show a human face prominently — this is a builder's tool

---

## What to Film / Record

**The demo page in action:**
- Go to signalloomai.com/ingest.html
- Paste a real YouTube URL (recommend something recognizable — a podcast clip, TED talk, or well-known interview)
- Show the JSON result appearing
- Record the browser window cleanly, no annotations needed

**The API in action:**
- Show a terminal with a curl request
- Show the JSON output
- Highlight the timestamp fields

**For the WebSocket section:**
- Record the streaming partial results in real-time
- Show the "done: false → done: true" progression

---

## Technical Contacts for Production Team

**For API access during filming:**
- Marketing firm should use the live demo at signalloomai.com/ingest.html (no account needed)
- For API filming, request a test API key from Signal Loom AI ops
- All whitepapers and technical specs: in SIGNAL-LOOM-SUPPORT-TRAINING.md

**Brand assets:**
- Logo: embedded in the site, SVG format available on request
- Color palette: Dark (#0a0a0f), Accent (#5B8DF9), Text (#E2E8F0), Dim (#94A3B8)
- Font: System sans (SF Pro / Inter / system-ui)

---

## Important Notes for the Production Team

1. **This is a technical audience.** The video should not talk down to viewers. They know what Whisper is. They know what RAG is. Don't define terms — demonstrate with precision.

2. **The demo is the product.** Nothing sells this better than seeing a YouTube URL become a structured JSON object in 30 seconds. Every second of demo is worth 10 seconds of narration.

3. **Do not reference competitors by name.** This video should stand on its own proof. If the differentiation from AssemblyAI or Deepgram needs to be made, make it through what we show — not what we say about them.

4. **The product is live and functional.** This is not vaporware or a concept video. Every feature shown in the video works today. The production team should feel confident demonstrating it live.

5. **There is no human narrator required.** This can be a clean voiceover + screen recording, or a simple talking-head CEO/founder — Traves's call. The content sells itself if the demo is clean.

---

*Brief prepared by Aster Vale, Chief of Staff — Signal Loom AI*
*For questions or assets: contact via this system or hello@signalloomai.com*
