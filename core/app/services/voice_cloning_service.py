from pathlib import Path
from synthesizer.inference import Synthesizer
from encoder import inference as encoder
from vocoder import inference as vocoder
import numpy as np
import librosa

class VoiceCloningService:
    def __init__(self):
        encoder.load_model(Path("encoder/saved_models/pretrained.pt"))
        self.synthesizer = Synthesizer(Path("synthesizer/saved_models/logs-pretrained/taco_pretrained"))
        vocoder.load_model(Path("vocoder/saved_models/pretrained/pretrained.pt"))

    def clone_voice(self, audio_file_path: str) -> bytes:
        """
        Clones a voice from an audio file and returns the synthesized audio.
        """
        # Load the audio file
        original_wav, sampling_rate = librosa.load(audio_file_path)
        preprocessed_wav = encoder.preprocess_wav(original_wav, sampling_rate)

        # Generate the embedding
        embed = encoder.embed_utterance(preprocessed_wav)

        # Synthesize the text
        text = "This is a test of the voice cloning system."
        specs = self.synthesizer.synthesize_spectrograms([text], [embed])

        # Generate the waveform
        generated_wav = vocoder.infer_waveform(specs[0])
        generated_wav = np.pad(generated_wav, (0, self.synthesizer.sample_rate), mode="constant")

        return generated_wav.tobytes()
