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
backend_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(backend_env_path):
    load_dotenv(dotenv_path=backend_env_path)

# Automatically load API key from root api.txt if present
api_txt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api.txt")
if os.path.exists(api_txt_path):
    try:
        with open(api_txt_path, "r", encoding="utf-8") as f:
            key_content = f.read().strip()
            if key_content:
                if key_content.startswith("gsk_"):
                    os.environ["GROQ_API_KEY"] = key_content
                    os.environ["LLM_PROVIDER"] = "groq"
                    print("Auto-configured Groq from api.txt")
                elif key_content.startswith("AIzaSy"):
                    os.environ["GEMINI_API_KEY"] = key_content
                    os.environ["LLM_PROVIDER"] = "gemini"
                    print("Auto-configured Gemini from api.txt")
    except Exception as e:
        print(f"Error reading api.txt: {e}")

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

def generate_offline_fallback(message: str, search_results: List[Dict[str, Any]], error_msg: Optional[str] = None, provider: str = "gemini") -> str:
    provider_name = provider.upper()
    key_name = "GROQ_API_KEY" if provider == "groq" else ("OPENROUTER_API_KEY" if provider == "openrouter" else "GEMINI_API_KEY")
    
    if not search_results:
        response_text = (
            "### 🩺 Clinical Analysis\n"
            "No clinical matches could be determined because the description did not contain recognizable symptoms.\n\n"
            "> [!WARNING]\n"
            "> Please enter a more detailed symptom description (e.g. 'Patient has shivering, fever fluctuating during the day, dry lips, headache' or 'Joint stiffness, swelling in knees, severe pain').\n"
        )
        if error_msg:
            response_text += f"\n> [!WARNING]\n> **{provider_name} API Call Failed**: {error_msg}\n> *Local offline search fallback triggered.*"
        else:
            response_text += (
                f"\n> [!NOTE]\n"
                f"> **{provider_name} API Key Missing**: You are currently in offline preview mode. To unlock interactive conversational analysis, please set the {key_name} environment variable on your system or place it in a `.env` file in the backend directory."
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
        mock_response += f"\n> [!WARNING]\n> **{provider_name} API Call Failed**: {error_msg}\n> *Fallen back to local search engine results.*"
    else:
        mock_response += (
            f"\n> [!NOTE]\n"
            f"> **{provider_name} API Key Missing**: You are currently in offline preview mode. To unlock interactive conversational analysis, please set the {key_name} environment variable on your system or place it in a `.env` file in the backend directory."
        )
    return mock_response

@app.post("/api/chat")
async def chat_diagnose(req: ChatRequest):
    # Determine LLM Provider
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    api_key = req.api_key or os.environ.get("GEMINI_API_KEY")
    
    # Auto-detect Groq keys from client input
    if req.api_key and req.api_key.startswith("gsk_"):
        provider = "groq"
    
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

    # If no api key is present and provider is gemini/groq/openrouter, trigger offline fallback
    if provider == "gemini" and not api_key:
        fallback_text = generate_offline_fallback(req.message, search_results, provider=provider)
        return {
            "response": fallback_text,
            "retrieved_diseases": search_results,
            "offline_mode": True
        }
    
    # 1. LOCAL OLLAMA PROVIDER (Zero Cost, Offline, No Keys)
    if provider == "ollama":
        try:
            import urllib.request
            messages = [
                {"role": "system", "content": system_prompt + "\n\n--- CLINICAL CONTEXT ---\n" + context_str + "\n--- END CLINICAL CONTEXT ---"}
            ]
            for msg in req.history:
                messages.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})
            messages.append({"role": "user", "content": req.message})

            ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
            payload = {
                "model": os.environ.get("OLLAMA_MODEL", "llama3"),
                "messages": messages,
                "stream": False
            }
            
            headers = {"Content-Type": "application/json"}
            url_req = urllib.request.Request(
                ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(url_req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
                return {
                    "response": res["message"]["content"],
                    "retrieved_diseases": search_results,
                    "offline_mode": False
                }
        except Exception as e:
            fallback_text = generate_offline_fallback(req.message, search_results, error_msg=f"Ollama local error: {str(e)}", provider=provider)
            return {
                "response": fallback_text,
                "retrieved_diseases": search_results,
                "offline_mode": True
            }

    # 2. FREE/LOW COST CLOUD PROVIDERS (Groq, OpenRouter) via standard HTTPS Request
    elif provider in ("groq", "openrouter"):
        try:
            import urllib.request
            messages = [
                {"role": "system", "content": system_prompt + "\n\n--- CLINICAL CONTEXT ---\n" + context_str + "\n--- END CLINICAL CONTEXT ---"}
            ]
            for msg in req.history:
                messages.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})
            messages.append({"role": "user", "content": req.message})

            if provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                auth_key = req.api_key or os.environ.get("GROQ_API_KEY")
                model_name = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
            else: # openrouter
                url = "https://openrouter.ai/api/v1/chat/completions"
                auth_key = os.environ.get("OPENROUTER_API_KEY")
                model_name = os.environ.get("OPENROUTER_MODEL", "google/gemma-2-9b-it:free")

            if not auth_key:
                raise ValueError(f"Missing API Key for provider: {provider.upper()}")

            payload = {
                "model": model_name,
                "messages": messages
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            url_req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(url_req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
                return {
                    "response": res["choices"][0]["message"]["content"],
                    "retrieved_diseases": search_results,
                    "offline_mode": False
                }
        except Exception as e:
            error_details = str(e)
            if hasattr(e, "read"):
                try:
                    error_details += " - " + e.read().decode("utf-8")
                except Exception:
                    pass
            print(f"Provider {provider.upper()} call failed: {error_details}")
            fallback_text = generate_offline_fallback(req.message, search_results, error_msg=f"{provider.upper()} API error: {error_details}", provider=provider)
            return {
                "response": fallback_text,
                "retrieved_diseases": search_results,
                "offline_mode": True
            }

    # 3. STANDARD GEMINI PROVIDER (Default)
    else:
        # Build complete prompt
        prompt = (
            f"{system_prompt}\n\n"
            f"--- CLINICAL CONTEXT ---\n"
            f"{context_str}\n"
            f"--- END CLINICAL CONTEXT ---\n\n"
            f"Patient Case Description: {req.message}\n"
        )
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            contents = []
            for msg in req.history:
                role = "user" if msg.role == "user" else "model"
                contents.append({"parts": [{"text": msg.content}], "role": role})
                
            contents.append({"parts": [{"text": prompt}], "role": "user"})
            
            response = model.generate_content(contents)
            return {
                "response": response.text,
                "retrieved_diseases": search_results,
                "offline_mode": False
            }
        except Exception as e:
            fallback_text = generate_offline_fallback(req.message, search_results, error_msg=str(e), provider=provider)
            return {
                "response": fallback_text,
                "retrieved_diseases": search_results,
                "offline_mode": True
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
