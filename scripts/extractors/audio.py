"""Pass 1 audio extraction: ffmpeg to 16 kHz mono WAV, then a local faster-whisper transcript."""

from __future__ import annotations

import gc
import json
import wave
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.config import Vault
from scripts.extractors import tools
from scripts.extractors.tools import fmt_time

TIME_MARKER = "<!-- t: {t} -->"
MARKER_EVERY = 30.0  # seconds between timestamp markers in the Markdown body
LOW_LOGPROB = -1.0
HIGH_NO_SPEECH = 0.6

Runner = Callable[[list[str]], str]


@dataclass
class Segment:
    start: float
    end: float
    text: str
    low_confidence: bool = False


Transcriber = Callable[[Path], tuple[list[Segment], str]]


@dataclass
class Transcript:
    segments: list[Segment]
    language: str
    duration: float
    model: str
    markdown: str
    paths: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)


def _load_wav(wav: Path) -> Any:
    """Read our own 16 kHz mono PCM WAV as float32. Avoids faster-whisper's PyAV decoder,
    which breaks with newer PyAV releases."""
    import numpy as np

    with wave.open(str(wav), "rb") as fh:
        frames = fh.readframes(fh.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


class WhisperTranscriber:
    """faster-whisper on the configured device, falling back to CPU if the GPU path fails."""

    def __init__(self, model: str, device: str, compute_type: str):
        self.model_name = model
        self._device = device
        self._compute_type = compute_type

    def __call__(self, wav: Path) -> tuple[list[Segment], str]:
        try:
            return self._run(wav, self._device, self._compute_type)
        except Exception:  # noqa: BLE001 - missing CUDA libs surface as assorted errors
            if self._device == "cpu":
                raise
            return self._run(wav, "cpu", "int8")

    def _run(self, wav: Path, device: str, compute_type: str) -> tuple[list[Segment], str]:
        from faster_whisper import WhisperModel  # lazy: heavy import

        model = WhisperModel(self.model_name, device=device, compute_type=compute_type)
        try:
            raw, info = model.transcribe(_load_wav(wav), vad_filter=True)
            segments = [
                Segment(
                    s.start,
                    s.end,
                    s.text.strip(),
                    low_confidence=s.avg_logprob < LOW_LOGPROB or s.no_speech_prob > HIGH_NO_SPEECH,
                )
                for s in raw
            ]
        finally:
            del model
            gc.collect()  # free VRAM before a vision model is loaded
        return segments, info.language


def default_transcriber(vault: Vault) -> Transcriber:
    cfg = vault.settings.get("transcription", {})
    return WhisperTranscriber(
        str(cfg.get("model", "small")),
        str(cfg.get("device", "cpu")),
        str(cfg.get("compute_type", "int8")),
    )


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    hours, rest = divmod(ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _markdown(segments: list[Segment]) -> str:
    parts: list[str] = []
    last_marker = -MARKER_EVERY
    for seg in segments:
        if seg.start - last_marker >= MARKER_EVERY:
            parts.append(TIME_MARKER.format(t=fmt_time(seg.start)))
            last_marker = seg.start
        parts.append(seg.text)
    return "\n\n".join(parts)


def transcribe(
    source: Path,
    vault: Vault,
    stem: str,
    transcriber: Transcriber | None = None,
    runner: Runner | None = None,
) -> Transcript:
    """Extract audio, transcribe it and write .txt/.srt/.json under processed/transcripts/."""
    runner = runner or tools.run_tool  # resolved at call time so tests can patch it
    out_dir = vault.root / "processed" / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / f"{stem}.wav"
    runner(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(source)]
        + ["-vn", "-ac", "1", "-ar", "16000", str(wav)]
    )

    transcriber = transcriber or default_transcriber(vault)
    segments, language = transcriber(wav)
    model = str(getattr(transcriber, "model_name", "custom"))
    segments = [s for s in segments if s.text.strip()]
    duration = max((s.end for s in segments), default=0.0)

    review = [f"Low-confidence speech around {fmt_time(s.start)}; check against the audio."
              for s in segments if s.low_confidence]  # fmt: skip
    if not segments:
        review.append("No speech detected in the audio.")

    (out_dir / f"{stem}.txt").write_text("\n".join(s.text for s in segments) + "\n", "utf-8")
    srt = "\n".join(
        f"{i}\n{_srt_time(s.start)} --> {_srt_time(s.end)}\n{s.text}\n"
        for i, s in enumerate(segments, 1)
    )
    (out_dir / f"{stem}.srt").write_text(srt, encoding="utf-8")
    data: dict[str, Any] = {
        "model": model,
        "language": language,
        "duration": duration,
        "segments": [
            {"start": s.start, "end": s.end, "text": s.text, "low_confidence": s.low_confidence}
            for s in segments
        ],
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")

    paths = [f"processed/transcripts/{stem}.{ext}" for ext in ("txt", "srt", "json")]
    return Transcript(segments, language, duration, model, _markdown(segments), paths, review)
