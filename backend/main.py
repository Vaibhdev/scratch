from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

from routers import auth, projects, documents, export

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Generation Platform API")

# CORS - Must be added BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(export.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Generation Platform API"}
