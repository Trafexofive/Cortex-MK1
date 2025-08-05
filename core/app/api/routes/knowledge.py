from fastapi import APIRouter, UploadFile, File, Form
from ...services.knowledge_builder import KnowledgeBuilderService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
knowledge_builder = KnowledgeBuilderService()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = Form(...)):
    content = await file.read()
    await knowledge_builder.add_document(user_id, file.filename, content)
    return {"filename": file.filename, "status": "uploaded"}
