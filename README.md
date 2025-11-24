# Generation Platform

A full-stack AI-powered web application for generating, refining, and exporting business documents (Word .docx and PowerPoint .pptx).

## Features
- **User Authentication**: Secure login and registration.
- **Project Management**: Create and manage document generation projects.
- **Document Configuration**: Choose between Word and PowerPoint, define outlines manually or via AI.
- **AI Content Generation**: Generate content for each section/slide using Gemini API.
- **Interactive Refinement**: Refine content with AI prompts, leave feedback.
- **Export**: Download final documents as .docx or .pptx.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite, Python-docx, Python-pptx, Google Generative AI.
- **Frontend**: React, Vite, TailwindCSS, Axios.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API Key

### Backend Setup
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Usage
1. Register a new account.
2. Create a new project from the dashboard.
3. Select document type and configure the outline.
4. Use the "Generate Content" button for each section.
5. Refine content as needed.
6. Click "Export" to download the file.
