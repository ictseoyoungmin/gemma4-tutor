"""Audio/TTS/STT placeholder module."""

from __future__ import annotations


class AudioPipelinePlaceholder:
    def transcribe(self, audio_path: str) -> str:
        return "TODO: connect faster-whisper or whisper.cpp"

    def synthesize(self, text: str) -> str:
        return "TODO: connect Piper or other local TTS backend"
