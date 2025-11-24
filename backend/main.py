from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

from .routers import auth, projects

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Generation Platform API")

app.include_router(auth.router)
app.include_router(projects.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Generation Platform API"}
