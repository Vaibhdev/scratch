from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

class SectionBase(BaseModel):
    title: str
    order: int
    content: Optional[str] = None

class SectionCreate(SectionBase):
    pass

class Section(SectionBase):
    id: int
    document_id: int
    feedback: Optional[str] = None
    comments: List[Any] = []
    refinement_history: List[Any] = []
    class Config:
        orm_mode = True

class DocumentBase(BaseModel):
    pass

class DocumentCreate(DocumentBase):
    sections: List[SectionCreate]

class Document(DocumentBase):
    id: int
    project_id: int
    sections: List[Section] = []
    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    document: Optional[Document] = None
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
