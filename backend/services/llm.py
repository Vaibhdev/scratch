import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def generate_content(prompt: str, context: str = "") -> str:
    if not API_KEY:
        return "Error: GEMINI_API_KEY not found."
    
    model = genai.GenerativeModel('gemini-pro')
    
    full_prompt = f"Context: {context}\n\nTask: {prompt}\n\nGenerate the content:"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error generating content: {str(e)}"

def generate_outline(topic: str, doc_type: str) -> list:
    if not API_KEY:
        return ["Error: GEMINI_API_KEY not found."]
        
    model = genai.GenerativeModel('gemini-pro')
    
    if doc_type == "docx":
        prompt = f"Generate a structured outline for a business document about '{topic}'. Return only a list of section headers, one per line."
    else:
        prompt = f"Generate a list of slide titles for a PowerPoint presentation about '{topic}'. Return only a list of titles, one per line."
        
    try:
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        return [line.strip().lstrip('- ').strip() for line in lines if line.strip()]
    except Exception as e:
        return [f"Error: {str(e)}"]
