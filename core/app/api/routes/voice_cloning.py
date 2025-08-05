from fastapi import APIRouter, UploadFile, File
from ...services.voice_cloning_service import VoiceCloningService
import tempfile

router = APIRouter(prefix="/voice-cloning", tags=["voice-cloning"])
voice_cloning_service = VoiceCloningService()

@router.post("/clone")
async def clone_voice(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        content = await file.read()
        temp_audio_file.write(content)
        temp_audio_file.flush()

        cloned_voice = voice_cloning_service.clone_voice(temp_audio_file.name)

    return {"cloned_voice": cloned_voice.hex()}
