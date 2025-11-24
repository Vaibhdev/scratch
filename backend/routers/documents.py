from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database, auth
from services import llm

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post("/{document_id}/sections", response_model=schemas.Section)
def create_section(document_id: int, section: schemas.SectionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verify ownership
    document = db.query(models.Document).join(models.Project).filter(models.Document.id == document_id, models.Project.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    db_section = models.Section(**section.dict(), document_id=document_id)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

@router.get("/{document_id}/sections", response_model=List[schemas.Section])
def read_sections(document_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    document = db.query(models.Document).join(models.Project).filter(models.Document.id == document_id, models.Project.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return db.query(models.Section).filter(models.Section.document_id == document_id).order_by(models.Section.order).all()

@router.post("/{document_id}/generate_outline")
def generate_outline(document_id: int, topic: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    document = db.query(models.Document).join(models.Project).filter(models.Document.id == document_id, models.Project.owner_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_type = document.project.document_type
    outline = llm.generate_outline(topic, doc_type)
    
    # Clear existing sections
    db.query(models.Section).filter(models.Section.document_id == document_id).delete()
    
    # Create new sections
    created_sections = []
    for i, title in enumerate(outline):
        section = models.Section(document_id=document_id, title=title, order=i, content="")
        db.add(section)
        created_sections.append(section)
    
    db.commit()
    return {"message": "Outline generated", "sections": [s.title for s in created_sections]}

@router.post("/sections/{section_id}/generate")
def generate_section_content(section_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    section = db.query(models.Section).join(models.Document).join(models.Project).filter(models.Section.id == section_id, models.Project.owner_id == current_user.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Context could include project description or previous sections
    context = f"Project: {section.document.project.title}. Section: {section.title}"
    content = llm.generate_content(f"Write content for section '{section.title}'", context)
    
    section.content = content
    db.commit()
    return {"content": content}

@router.post("/sections/{section_id}/refine")
def refine_section_content(section_id: int, prompt: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    section = db.query(models.Section).join(models.Document).join(models.Project).filter(models.Section.id == section_id, models.Project.owner_id == current_user.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Save current content to history
    history_item = {
        "prompt": prompt,
        "content": section.content,
        "timestamp": str(datetime.utcnow())
    }
    # Append to history (need to handle JSON list update properly)
    if section.refinement_history is None:
        section.refinement_history = []
    
    # Create a new list to ensure SQLAlchemy detects the change
    new_history = list(section.refinement_history)
    new_history.append(history_item)
    section.refinement_history = new_history
    
    context = f"Original content: {section.content}"
    new_content = llm.generate_content(prompt, context)
    
    section.content = new_content
    db.commit()
    return {"content": new_content}
