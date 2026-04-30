# Kokoro TTS Platform PRD (Unix-Based, CPU-Optimized)

## 1. Overview

A self-hosted Text-to-Speech (TTS) platform built on Kokoro TTS, designed for Unix environments. The system enables:

- English-only voice synthesis
- User-controlled speech customization
- Real-time preview generation
- MP3 export and download
- Accurate generation time estimation
- CPU-first deployment (no GPU required)

---

## 2. Goals

### Primary Goals
- Reliable CPU-based TTS generation
- Predictable performance and timing
- Customizable speech output
- Scalable backend architecture

### Secondary Goals
- Preview-first UX
- Efficient caching and reuse
- Async processing for long jobs

---

## 3. Non-Goals

- Emotion-level synthesis (limited by model)
- Voice cloning or training
- Multilingual support
- Studio-grade prosody control

---

## 4. System Architecture

### High-Level Flow

```

User Input
↓
Text Analyzer (length + estimate)
↓
Preview Generator (short clip)
↓
TTS Engine (Kokoro)
↓
Audio Processor (WAV → MP3)
↓
Storage + Download API

```

---

## 5. Core Components

### API Layer
- FastAPI
- Handles:
  - text input
  - parameters
  - preview requests
  - job creation

### TTS Engine
- Kokoro ONNX model
- Loaded into memory at startup

### Audio Processing
- FFmpeg for conversion:
```

ffmpeg -i input.wav -codec:a libmp3lame -b:a 192k output.mp3

```

### Job Queue
- Redis-based queue
- Worker processes (2–4 per machine)

### Storage
```

/audio/{user_id}/{job_id}.mp3

```

---

## 6. CPU-Only Deployment Strategy

### Key Insight
Kokoro is CPU-friendly and does NOT require a GPU.

### Performance Characteristics

| Mode | Speed |
|------|------|
| CPU | ~0.8x – 1.5x realtime |
| GPU (optional) | ~3x – 10x realtime |

---

## 7. Performance Expectations (CPU)

| Input Size | Audio Length | Generation Time |
|-----------|-------------|----------------|
| 50 words | ~20 sec | 15–25 sec |
| 300 words | ~2 min | 1.5–3 min |
| 2000 words | ~12–15 min | 10–20 min |

---

## 8. System Constraints Without GPU

### Limitations
- Slower generation speed
- Limited concurrency (1–4 jobs)
- Long jobs must be asynchronous
- Not suitable for real-time full-length output

### Still Fully Supported
- Preview generation
- MP3 export
- Parameter customization
- Time estimation

---

## 9. Required Design Adjustments (CPU Optimization)

### 1. Async Job Processing (MANDATORY)

```

POST /generate → returns job_id
GET /status → progress
GET /download → file

```

---

### 2. Job Queue

- Redis queue
- Worker pool (2–4 workers)
- FIFO + priority support

---

### 3. Text Chunking (CRITICAL)

Split long inputs:

```

Max chunk size: ~500 words

```

Pipeline:
```

Split → Generate in parallel → Merge audio

```

---

### 4. Preview-First UX

- Generate first 3–8 seconds
- Response time: <1 second
- Prevents wasted compute

---

### 5. Caching

Hash key:
```

hash(text + voice + parameters)

```

Reuse identical outputs.

---

## 10. User Customization

### Voice Selection
- Predefined voices:
  - af_bella
  - am_adam
  - etc.

---

### Adjustable Parameters

| Parameter | Method |
|----------|--------|
| Speed | Native |
| Pitch | FFmpeg post-processing |
| Tone | Text formatting |
| Energy | Audio filters |

---

### Processing Pipeline

```

Kokoro WAV
↓
Pitch shift (ffmpeg)
↓
Tempo adjust
↓
MP3 encode

```

---

## 11. Preview Feature

### Behavior
- Uses truncated input (~200 chars)
- Returns short audio clip

### Target Latency
- < 1 second

---

## 12. Time Estimation Engine

### Formula

```

words = len(text.split())
speech_duration = words / 2.7
generation_time = speech_duration / speed_factor

````

---

### Example

| Words | Audio | CPU Time |
|------|------|---------|
| 270 | ~100 sec | ~90–110 sec |

---

### API Response

```json
{
  "estimated_audio_length_sec": 100,
  "estimated_generation_time_sec": 95,
  "processing_mode": "cpu"
}
````

---

## 13. API Design

### Preview

```
POST /preview
```

### Estimate

```
POST /estimate
```

### Generate

```
POST /generate
```

### Status

```
GET /status/{job_id}
```

### Download

```
GET /download/{job_id}
```

---

## 14. File Output

### Formats

| Format | Purpose      |
| ------ | ------------ |
| WAV    | intermediate |
| MP3    | final        |

---

### File Sizes

| Length | Size    |
| ------ | ------- |
| 1 min  | ~1.5 MB |
| 10 min | ~15 MB  |

---

## 15. Hardware Requirements

### Minimum

* 2 vCPU
* 4 GB RAM

### Recommended

* 4–8 vCPU
* 8–16 GB RAM

---

## 16. Scaling Strategy

### Phase 1 (CPU Only)

* Single instance
* 2–4 workers
* Redis queue

### Phase 2

* Horizontal scaling
* Load balancer
* Shared storage

### Phase 3 (Optional GPU)

* Add GPU worker node
* Route large jobs selectively

---

## 17. Smart Features

### Chunk Parallelization

* Major CPU performance boost

### Job Prioritization

* Short jobs first

### Caching Layer

* Avoid recomputation

---

## 18. Limitations

* No fine-grained emotional control
* Limited voice library
* Pitch/tone are approximations
* Long jobs require async handling

---

## 19. Recommended Stack

* FastAPI
* ONNX Runtime
* Redis
* FFmpeg
* Gunicorn

---

## 20. Final Positioning

This system should be treated as:

> A CPU-optimized, async TTS generation platform with real-time preview capabilities

NOT:

> A fully real-time, instant full-length speech system

---

## 21. Future Enhancements

* GPU acceleration node
* Streaming audio playback
* Voice blending
* UI dashboard
* Batch processing tools

---
