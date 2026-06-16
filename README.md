# NIdan_bot: Ayurvedic Clinical Diagnostics & RAG Assistant

NIdan_bot is a high-performance clinical decision support system designed to assist practitioners in performing differential diagnosis (*Nidana*) based on the classical Ayurvedic text **Madhava Nidana** (Chapters 1-32).

The system integrates a local TF-IDF search engine indexing classical verses and symptoms with Google's Gemini generative AI using a Retrieval-Augmented Generation (RAG) pipeline to deliver precise, citation-backed diagnostic assessments.

---

## Key Features

- **Ayurvedic Botanical UI**: A premium, mobile-native interface themed with rich forest greens, gold/saffron accents, and sandalwood parchment.
- **Adaptive Mobile View**: Automatically converts into a native-app-style interface on smaller screens with a clean tab bar (`Logger`, `Consultation`, and `Differential`).
- **One-Click Case Loader**: Load classical symptom profiles (like *Jvara*, *Amavata*, *Kamala*, *Gridhrasi*, and *Asmari*) instantly for demonstration and testing.
- **Intelligent Key Bindings**: Press `Enter` in the logger to instantly query the diagnostics engine and focus directly on consultation chat.
- **RAG-Backed Consultation**: Generates detailed diagnosis proposals (matching confidence, pathogenesis/*Samprapti*, and affected *srotas*) cross-referenced with textual chapters.
- **Robust Offline Fallback**: Features a local fallback mechanism that continues to serve TF-IDF match data if the Gemini API is unreachable or key is missing.

---

## Project Structure

```text
NIdan_bot/
├── backend/               # FastAPI application
│   ├── data/              # Indexed diseases database & raw files
│   ├── main.py            # API server and RAG controller
│   ├── search_engine.py   # TF-IDF local retrieval implementation
│   ├── requirements.txt   # Python packages
│   └── .env               # Secrets configuration (API Key)
├── frontend/              # React Vite application
│   ├── src/               # React components and styling (App.css, App.jsx)
│   ├── package.json       # JS dependencies
│   └── index.html         # Application entrypoint
├── knowledgebase/         # Reference text files
├── docker-compose.yml     # Unified container orchestration
└── README.md              # Project documentation
```

---

## Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
5. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend server will start at `http://127.0.0.1:8000`.

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173/` in your web browser.

---

## Deployment with Docker

You can run the entire system inside containerized environments using Docker and Docker Compose.

### Build and Run with Docker Compose
1. Ensure your `backend/.env` file exists with a valid `GEMINI_API_KEY`.
2. Build and launch the containers:
   ```bash
   docker-compose up --build -d
   ```
3. Access the dashboard:
   - Frontend: `http://localhost` (Port 80)
   - Backend: `http://localhost:8000`

---

## Classical References
Textual databases and context are sourced from **Madhava Nidana**, compiled by *Madhakara* (circa 7th century CE), focusing on Chapters 1 through 32 covering diagnostic guidelines for systemic and organ-specific imbalances.
