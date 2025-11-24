from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .. import models, database, auth
from ..services import export

router = APIRouter(
    prefix="/export",
    tags=["export"],
)

@router.get("/{document_id}")
def export_document(document_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    document = db.query(models.Document).join(models.Project).filter(models.Document.id == document_id, models.Project.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_type = document.project.document_type
    
    if doc_type == "docx":
        file_stream = export.create_docx(document)
        filename = f"{document.project.title}.docx"
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif doc_type == "pptx":
        file_stream = export.create_pptx(document)
        filename = f"{document.project.title}.pptx"
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    else:
        raise HTTPException(status_code=400, detail="Invalid document type")
        
    return StreamingResponse(
        file_stream, 
        media_type=media_type, 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
