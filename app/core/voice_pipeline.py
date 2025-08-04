import asyncio
import numpy as np
from typing import AsyncGenerator
import subprocess
import tempfile
import os

class VoicePipeline:
    def __init__(self):
        self.whisper_path = "./voice/whisper.cpp/main"
        self.whisper_model = "./voice/whisper.cpp/models/ggml-base.en.bin"
        self.piper_voice = "./voice/piper/voices/en_US-lessac-medium.onnx"
        
    async def transcribe_streaming(self, audio_stream: AsyncGenerator) -> AsyncGenerator[str, None]:
        """Stream transcription with <200ms latency"""
        buffer = []
        
        async for audio_chunk in audio_stream:
            buffer.extend(audio_chunk)
            
            if len(buffer) >= 8000:  # ~500ms of audio at 16kHz
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    self._save_wav(buffer, f.name)
                    
                    # Transcribe with whisper.cpp
                    result = subprocess.run([
                        self.whisper_path, 
                        self.whisper_model, 
                        f.name
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        yield result.stdout.strip()
                    
                    os.unlink(f.name)
                
                buffer = buffer[-1600:]  # Keep 100ms overlap
    
    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream TTS synthesis with ~50ms latency"""
        # Use Piper for fast, human-like synthesis
        process = subprocess.Popen([
            'piper', '--model', self.piper_voice, 
            '--output_file', '-'
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        
        process.stdin.write(text.encode())
        process.stdin.close()
        
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                break
            yield chunk
    
    def _save_wav(self, audio_data, filename):
        """Save audio buffer as WAV file"""
        import wave
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(np.array(audio_data, dtype=np.int16).tobytes())