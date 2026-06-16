import os
import json
from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

from search_engine import NidanaSearchEngine

# Load environment variables
load_dotenv()

app = FastAPI(title="NIdan_bot API", description="Ayurvedic Diagnostics RAG & Chatbot Backend")

# Enable CORS for the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Search Engine
search_engine = NidanaSearchEngine()

# Raw chapters cache
raw_chapters = []
chapters_path = os.path.join(os.path.dirname(__file__), "data", "raw_chapters.json")
if os.path.exists(chapters_path):
    with open(chapters_path, "r", encoding="utf-8") as f:
        raw_chapters = json.load(f)
    print(f"Loaded {len(raw_chapters)} raw chapters for reference lookup.")

class ChatMessage(BaseModel):
    role: str  # "user" or "model" / "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    api_key: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    top_n: int = 5

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "NIdan_bot backend is running", "diseases_count": len(search_engine.diseases)}

@app.get("/api/diseases")
def list_diseases():
    return search_engine.diseases

@app.get("/api/chapters")
def list_chapters():
    return [{"chapter_number": ch["chapter_number"], "chapter_title": ch["chapter_title"], "chapter_type": ch["chapter_type"], "start_page": ch["start_page"], "end_page": ch["end_page"]} for ch in raw_chapters]

@app.get("/api/chapters/{chapter_num}")
def get_chapter(chapter_num: int):
    for ch in raw_chapters:
        if ch["chapter_number"] == chapter_num:
            return ch
    raise HTTPException(status_code=404, detail="Chapter not found")

@app.post("/api/search")
def search_diseases(req: SearchRequest):
    try:
        results = search_engine.search(req.query, top_n=req.top_n)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_offline_fallback(message: str, search_results: List[Dict[str, Any]], error_msg: Optional[str] = None) -> str:
    if not search_results:
        response_text = (
            "### 🩺 Clinical Analysis\n"
            "No clinical matches could be determined because the description did not contain recognizable symptoms.\n\n"
            "> [!WARNING]\n"
            "> Please enter a more detailed symptom description (e.g. 'Patient has shivering, fever fluctuating during the day, dry lips, headache' or 'Joint stiffness, swelling in knees, severe pain').\n"
        )
        if error_msg:
            response_text += f"\n> [!WARNING]\n> **Gemini API Call Failed**: {error_msg}\n> *Local offline search fallback triggered.*"
        else:
            response_text += (
                f"\n> [!NOTE]\n"
                f"> **Gemini API Key Missing**: You are currently in offline preview mode. To unlock interactive conversational analysis, please set the GEMINI_API_KEY environment variable on your system or place it in a `.env` file in the backend directory."
            )
        return response_text

    primary = search_results[0]["disease"]
    matched_terms = [m["matched_term"] for m in search_results[0]["matched_symptoms"]]
    matched_str = ", ".join(matched_terms) if matched_terms else "Direct text match"
    
    mock_response = (
        f"### 🩺 Clinical Analysis\n"
        f"Based on the local semantic search, the patient's presentation shows a strong correlation with **{primary['roga']}** (Score: {search_results[0]['score'] * 100:.1f}%).\n"
        f"Key matching symptoms observed: *{matched_str}*.\n\n"
        f"### 📋 Differential Diagnoses\n"
    )
    
    for r in search_results:
        confidence = "High" if r["score"] > 0.6 else ("Medium" if r["score"] > 0.3 else "Low")
        mock_response += f"- **{r['disease']['roga']}** (Confidence: **{confidence}** - {r['score']*100:.1f}% match)\n"
        
    mock_response += (
        f"\n### 🔬 Pathophysiological Profile (Dosha, Dushya, Srotas)\n"
        f"- **Vitiated Dosha**: {', '.join(primary['dosha'])}\n"
        f"- **Dushya involved**: {', '.join(primary['dushya'])}\n"
        f"- **Srotas affected**: {', '.join(primary['srotas'])}\n"
        f"- **Agni state**: {', '.join(primary.get('agni', ['Manda']))}\n"
        f"- **Samprapti (Pathogenesis)**: {primary['samprapti']}\n\n"
        f"### 🥣 Pathya / Apathya Guidelines\n"
        f"**Recommended (Pathya)**:\n"
    )
    for p in primary["pathya"]:
        mock_response += f"- {p}\n"
    mock_response += "\n**Prohibited (Apathya)**:\n"
    for a in primary["apathya"]:
        mock_response += f"- {a}\n"
        
    mock_response += (
        f"\n### 📚 Classical Excerpts & References\n"
        f"- **References**: {', '.join(primary['classical_references'])}\n"
        f"- **Treatments**: {', '.join(primary['chikitsa_references'])}\n"
    )

    if error_msg:
        mock_response += f"\n> [!WARNING]\n> **Gemini API Call Failed**: {error_msg}\n> *Fallen back to local search engine results.*"
    else:
        mock_response += (
            f"\n> [!NOTE]\n"
            f"> **Gemini API Key Missing**: You are currently in offline preview mode. To unlock interactive conversational analysis, please set the GEMINI_API_KEY environment variable on your system or place it in a `.env` file in the backend directory."
        )
        
    return mock_response

@app.post("/api/chat")
async def chat_diagnose(req: ChatRequest):
    # Determine which API key to use
    api_key = req.api_key or os.environ.get("GEMINI_API_KEY")
    
    # Run RAG Search to get relevant disease files
    search_results = search_engine.search(req.message, top_n=3)
    
    # Formulate context for the LLM
    context_str = ""
    if search_results:
        context_str = "RELEVANT CLINICAL DISEASES EXTRACTED FROM MADHAVA NIDANA:\n\n"
        for idx, result in enumerate(search_results):
            d = result["disease"]
            context_str += (
                f"[{idx+1}] Disease (Roga): {d['roga']}\n"
                f"  - Score: {result['score']}\n"
                f"  - Dosha: {', '.join(d['dosha'])}\n"
                f"  - Dushya: {', '.join(d['dushya'])}\n"
                f"  - Srotas: {', '.join(d['srotas'])}\n"
                f"  - Pathogenesis (Samprapti): {d['samprapti']}\n"
                f"  - Symptoms (Lakshana): {', '.join(d['lakshana'])}\n"
                f"  - Diet recommendations (Pathya): {', '.join(d['pathya'])}\n"
                f"  - Diet prohibited (Apathya): {', '.join(d['apathya'])}\n"
                f"  - Classical references: {', '.join(d['classical_references'])}\n\n"
            )
            
    # System prompt for clinical diagnostics
    system_prompt = (
        "You are an expert Ayurvedic Clinical Diagnostic Assistant. Your task is to analyze the patient's symptoms described by the doctor, "
        "cross-reference them with the classical disease profiles from Madhava Nidana provided in the context, and generate a structured clinical report.\n\n"
        "RULES:\n"
        "1. Prioritize diseases from the provided context. Show matching symptoms clearly.\n"
        "2. Keep Sanskrit terms exact.\n"
        "3. Provide a clear differential diagnosis with confidence levels (High, Medium, Low).\n"
        "4. Recommend Pathya (do's) and Apathya (don'ts) based on the matching diseases.\n"
        "5. Explain the Samprapti (pathogenesis) of the primary suspect disease based on the text.\n"
        "6. If you cannot find a strong match, state it clearly. Do not make up external information.\n\n"
        "Format your response in beautiful markdown with clinical headers like:\n"
        "### 🩺 Clinical Analysis\n"
        "### 📋 Differential Diagnoses\n"
        "### 🔬 Pathophysiological Profile (Dosha, Dushya, Srotas)\n"
        "### 🥣 Pathya / Apathya Guidelines\n"
        "### 📚 Classical Excerpts & References\n"
    )
    
    # Build complete prompt
    prompt = (
        f"{system_prompt}\n\n"
        f"--- CLINICAL CONTEXT ---\n"
        f"{context_str}\n"
        f"--- END CLINICAL CONTEXT ---\n\n"
        f"Patient Case Description: {req.message}\n"
    )

    if not api_key:
        fallback_text = generate_offline_fallback(req.message, search_results)
        return {
            "response": fallback_text,
            "retrieved_diseases": search_results,
            "offline_mode": True
        }
    
    # Call Gemini API
    try:
        genai.configure(api_key=api_key)
        # We can use 'gemini-2.5-flash' for fast and accurate responses
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build chat history for Gemini API
        contents = []
        for msg in req.history:
            role = "user" if msg.role == "user" else "model"
            contents.append({"parts": [{"text": msg.content}], "role": role})
            
        # Append current prompt
        contents.append({"parts": [{"text": prompt}], "role": "user"})
        
        response = model.generate_content(contents)
        return {
            "response": response.text,
            "retrieved_diseases": search_results,
            "offline_mode": False
        }
    except Exception as e:
        fallback_text = generate_offline_fallback(req.message, search_results, error_msg=str(e))
        return {
            "response": fallback_text,
            "retrieved_diseases": search_results,
            "offline_mode": True
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
