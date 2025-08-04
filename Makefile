.PHONY: build-whisper setup-piper download-models start-voice-agent

build-whisper:
	cd voice/whisper.cpp && make clean && make

setup-piper:
	pip install piper-tts
	mkdir -p voice/piper/voices

download-models:
	# Download Whisper base.en model
	wget -P voice/whisper.cpp/models/ https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
	# Download Piper voice
	wget -P voice/piper/voices/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

start-voice-agent:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	python voice/voice_bridge.py

test-latency:
	python scripts/benchmark_latency.py

clean:
	cd voice/whisper.cpp && make clean
	rm -rf voice/piper/voices/*.onnx