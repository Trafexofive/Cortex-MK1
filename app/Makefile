.PHONY: build-whisper download-models

build-whisper:
	cd voice/whisper.cpp && make clean && make

download-models:
	# Download Whisper base.en model
	wget -P voice/whisper.cpp/models/ https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
	# Download Piper voice
	wget -P voice/piper/voices/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
