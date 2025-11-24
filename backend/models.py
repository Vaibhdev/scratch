from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    document_type = Column(String) # "docx" or "pptx"
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="projects")
    document = relationship("Document", back_populates="project", uselist=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    project = relationship("Project", back_populates="document")
    sections = relationship("Section", back_populates="document")

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    order = Column(Integer)
    title = Column(String) # Section header or Slide title
    content = Column(Text, nullable=True) # Generated content
    
    # For refinement
    refinement_history = Column(JSON, default=list) # List of {prompt, content, timestamp}
    comments = Column(JSON, default=list) # List of {text, timestamp}
    feedback = Column(String, nullable=True) # "like", "dislike"

    document = relationship("Document", back_populates="sections")
