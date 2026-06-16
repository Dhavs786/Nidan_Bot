import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Grouped Ayurvedic & Modern symptoms for doctor's quick selection
const SYMPTOM_CATEGORIES = [
  {
    category: "Jvara (Fever & Systemic)",
    symptoms: [
      { label: "Shivering (Vepathu)", term: "shivering" },
      { label: "High Fever (Tiksna Vega)", term: "high-grade fever" },
      { label: "Low Fever (Manda Vega)", term: "low-grade fever" },
      { label: "Dry Lips/Throat (Sosa)", term: "dry throat and lips" },
      { label: "Insomnia (Nidranasa)", term: "insomnia" },
      { label: "Headache (Siro-ruk)", term: "headache" },
      { label: "Body Aches (Gatra-ruk)", term: "body aches" }
    ]
  },
  {
    category: "Agni & Koshtha (Digestive)",
    symptoms: [
      { label: "Constipation (Vit-bandha)", term: "constipation" },
      { label: "Loose Stools (Atisarana)", term: "loose stools" },
      { label: "Vomiting (Chardi)", term: "vomiting" },
      { label: "Nausea (Hrllasa)", term: "nausea" },
      { label: "Indigestion (Apaka)", term: "indigestion" },
      { label: "Burning Epigastrium", term: "burning sensation" },
      { label: "Intense Thirst (Trsna)", term: "thirst" }
    ]
  },
  {
    category: "Asthi & Sandhi (Joints/Bones)",
    symptoms: [
      { label: "Joint Pain (Sandhi-ruk)", term: "joint pain" },
      { label: "Joint Swelling (Sotha)", term: "joint swelling" },
      { label: "Morning Stiffness (Stambha)", term: "morning stiffness" },
      { label: "Radiating Leg Pain", term: "radiating pain from hip down the leg" },
      { label: "Numbness (Suptata)", term: "numbness" }
    ]
  },
  {
    category: "Mutra & Basti (Urinary)",
    symptoms: [
      { label: "Difficulty Urinating (Krcchra)", term: "difficulty urinating" },
      { label: "Urinary Blockage", term: "urinary obstruction" },
      { label: "Blood in Urine (Rakta-mutra)", term: "blood in urine" },
      { label: "Turbid Urine", term: "turbid urine" }
    ]
  },
  {
    category: "Pranavaha (Respiratory)",
    symptoms: [
      { label: "Cough (Kasa)", term: "cough" },
      { label: "Wheezing (Ghurghuraka)", term: "wheezing" },
      { label: "Shortness of Breath", term: "breathlessness" }
    ]
  },
  {
    category: "Twak & Nayana (Skin/Eyes)",
    symptoms: [
      { label: "Yellow Skin/Eyes (Kamala)", term: "yellow discoloration of skin and eyes" },
      { label: "Sweating (Sveda)", term: "excessive sweating" }
    ]
  }
];

// Predefined Classical Clinical Case Examples
const CLINICAL_EXAMPLES = [
  {
    name: "Jvara (Fever)",
    text: "Patient presents with shivering, fluctuating high fever spikes, dry lips and throat, sleeplessness at night, and severe headache."
  },
  {
    name: "Amavata (Rheumatoid)",
    text: "Patient complains of severe joint pain in hands and knees resembling scorpion stings, morning stiffness, joint swelling, and indigestion."
  },
  {
    name: "Kamala (Jaundice)",
    text: "Patient has yellow discoloration of eyes and skin, dark yellow-red urine, loss of appetite, and general weakness."
  },
  {
    name: "Gridhrasi (Sciatica)",
    text: "Patient describes radiating pain starting from the hip down through the waist, thigh, knee, and calf to the foot, with numbness and stiffness in the leg."
  },
  {
    name: "Asmari (Renal Stone)",
    text: "Patient reports radiating pain in the bladder, perineum, and penis, with difficulty passing urine, sudden stoppage of urinary flow, and blood in urine."
  }
];

const BACKEND_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [caseText, setCaseText] = useState("");
  const [activeTab, setActiveTab] = useState("diagnosis");
  const [chatHistory, setChatHistory] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [chapterContent, setChapterContent] = useState("");
  const [loadingChapter, setLoadingChapter] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [offlineMode, setOfflineMode] = useState(true);
  const [activeMobileTab, setActiveMobileTab] = useState("input");

  const chatEndRef = useRef(null);

  // Check Backend and Load Chapters on Mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/health`);
        if (res.ok) {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch (err) {
        setBackendStatus("offline");
      }
    };

    const fetchChapters = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/chapters`);
        if (res.ok) {
          const data = await res.json();
          setChapters(data);
        }
      } catch (err) {
        console.error("Failed to fetch chapters", err);
      }
    };

    checkHealth();
    fetchChapters();
  }, []);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Toggle quick symptom chip
  const handleSymptomToggle = (term) => {
    const normalizedCase = caseText.toLowerCase();
    const normalizedTerm = term.toLowerCase();
    
    if (normalizedCase.includes(normalizedTerm)) {
      // Create a regex to match the term, optionally with leading/trailing commas
      const regex = new RegExp(`\\b${term}\\b,?\\s*|\\s*,?\\s*\\b${term}\\b`, 'gi');
      let updated = caseText.replace(regex, "").trim();
      // Remove trailing commas if any
      if (updated.endsWith(",")) {
        updated = updated.slice(0, -1).trim();
      }
      setCaseText(updated);
    } else {
      const prefix = caseText.trim() ? (caseText.trim().endsWith(",") ? " " : ", ") : "";
      setCaseText(caseText.trim() + prefix + term);
    }
  };

  // Perform main diagnostic search and analysis
  const handleAnalyze = async () => {
    if (!caseText.trim()) return;

    setLoading(true);
    setActiveMobileTab("chat"); // Auto-switch mobile view to chat panel to show progress
    setChatHistory([]); // Reset history on new case analysis
    setSearchResults([]);

    try {
      // 1. Fetch RAG Search results for the panel
      const searchRes = await fetch(`${BACKEND_URL}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: caseText, top_n: 5 })
      });
      if (searchRes.ok) {
        const searchData = await searchRes.json();
        setSearchResults(searchData);
      }

      // 2. Fetch Chat Diagnostic assessment
      const chatRes = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: caseText,
          history: [],
          api_key: null
        })
      });

      if (chatRes.ok) {
        const chatData = await chatRes.json();
        setOfflineMode(chatData.offline_mode);
        setChatHistory([
          { role: "user", content: caseText },
          { role: "model", content: chatData.response }
        ]);
        setActiveTab("diagnosis");
      }
    } catch (err) {
      console.error(err);
      setChatHistory([
        { role: "user", content: caseText },
        { role: "model", content: "### ❌ Error\nFailed to connect to NIdan_bot diagnosis engine. Make sure the FastAPI backend is running." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Send follow-up chat message
  const handleSendMessage = async () => {
    if (!chatMessage.trim() || loading) return;

    const userMsg = chatMessage;
    setChatMessage("");
    
    const updatedHistory = [...chatHistory, { role: "user", content: userMsg }];
    setChatHistory(updatedHistory);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          history: updatedHistory.slice(0, -1),
          api_key: null
        })
      });

      if (res.ok) {
        const data = await res.json();
        setOfflineMode(data.offline_mode);
        setChatHistory([...updatedHistory, { role: "model", content: data.response }]);
      }
    } catch (err) {
      console.error(err);
      setChatHistory([...updatedHistory, { role: "model", content: "### ❌ Error\nCould not receive reply. Check your connection." }]);
    } finally {
      setLoading(false);
    }
  };

  // View full classical chapter
  const handleSelectChapter = async (chNum) => {
    setSelectedChapter(chNum);
    setLoadingChapter(true);
    setChapterContent("");
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/chapters/${chNum}`);
      if (res.ok) {
        const data = await res.json();
        setChapterContent(data.content);
      }
    } catch (err) {
      console.error("Failed to load chapter", err);
      setChapterContent("Failed to load chapter content.");
    } finally {
      setLoadingChapter(false);
    }
  };

  // Parse markdown into simple HTML elements for display in chat bubbles
  const renderMarkdown = (text) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Alerts
      if (line.startsWith('> [!NOTE]')) {
        return <blockquote key={idx} className="alert note"><strong>Note:</strong> {line.replace('> [!NOTE]', '').trim()}</blockquote>;
      }
      if (line.startsWith('> [!WARNING]')) {
        return <blockquote key={idx} className="alert warning"><strong>Warning:</strong> {line.replace('> [!WARNING]', '').trim()}</blockquote>;
      }
      if (line.startsWith('> [!IMPORTANT]')) {
        return <blockquote key={idx} className="alert important"><strong>Important:</strong> {line.replace('> [!IMPORTANT]', '').trim()}</blockquote>;
      }
      if (line.startsWith('>')) {
        return <blockquote key={idx}>{line.replace(/^>\s*/, '')}</blockquote>;
      }
      
      // Headers
      if (line.startsWith('### ')) {
        return <h3 key={idx}>{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx}>{line.replace('## ', '')}</h2>;
      }
      if (line.startsWith('# ')) {
        return <h1 key={idx}>{line.replace('# ', '')}</h1>;
      }
      
      // List items
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const cleanLine = line.substring(2);
        return <li key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(cleanLine) }} />;
      }
      
      // Normal lines
      if (line.trim() === '') return <div key={idx} style={{ height: '8px' }}></div>;
      
      return <p key={idx} dangerouslySetInnerHTML={{ __html: parseInlineStyles(line) }} />;
    });
  };

  const parseInlineStyles = (text) => {
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return formatted;
  };

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo-icon">न</div>
          <div className="logo-text">
            <h1>NIdan_bot</h1>
            <span>Madhava Nidana Clinical RAG System</span>
          </div>
        </div>
        <div className="header-right">
          <div className="status-indicator">
            <span className={`status-dot ${backendStatus === 'online' ? '' : 'offline'}`}></span>
            System Status: {backendStatus === 'online' ? 'Online' : 'Disconnected'}
          </div>
          {offlineMode && chatHistory.length > 0 && (
            <div className="status-indicator" style={{ borderColor: 'var(--color-gold)' }}>
              <span className="status-dot" style={{ backgroundColor: 'var(--color-gold)', boxShadow: '0 0 8px var(--color-gold)' }}></span>
              Mode: Local Engine
            </div>
          )}
        </div>
      </header>

      {/* Mobile navigation tab-bar */}
      <div className="mobile-view-tabs">
        <button
          className={`mobile-tab-btn ${activeMobileTab === 'input' ? 'active' : ''}`}
          onClick={() => setActiveMobileTab('input')}
        >
          <span className="mobile-tab-icon">📝</span>
          Logger
        </button>
        <button
          className={`mobile-tab-btn ${activeMobileTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveMobileTab('chat')}
        >
          <span className="mobile-tab-icon">🏺</span>
          Consultation
        </button>
        <button
          className={`mobile-tab-btn ${activeMobileTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveMobileTab('results')}
        >
          <span className="mobile-tab-icon">🔬</span>
          Differential
        </button>
      </div>

      {/* Main Workspace Layout */}
      <main className={`workspace-grid show-${activeMobileTab}`}>
        
        {/* Left Column: Patient Case Input */}
        <section className="panel glass panel-input">
          <div className="panel-header">
            <div className="panel-title">
              <span className="panel-title-icon">📝</span>
              Ayurvedic Case Logger
            </div>
          </div>
          <div className="panel-body">
            
            {/* Example Case Loading dropdown/buttons */}
            <div className="example-selector-box">
              <div className="example-label">
                <span>📚</span> Load Example Case Profile
              </div>
              <div className="example-buttons">
                {CLINICAL_EXAMPLES.map((ex, idx) => (
                  <button
                    key={idx}
                    className="btn-example"
                    onClick={() => setCaseText(ex.text)}
                  >
                    {ex.name}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              className="case-textarea"
              placeholder="Describe the patient's presentation here (English or Sanskrit terms)...&#10;e.g., 'Patient has high fever and shivering, dry throat, and headache...'&#10;&#10;Press ENTER to run diagnosis, SHIFT+ENTER for new line."
              value={caseText}
              onChange={(e) => setCaseText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAnalyze();
                }
              }}
            />

            {/* Perform Differential Nidana Button positioned DIRECTLY below the textarea */}
            <button
              className="btn-analyze"
              disabled={loading || !caseText.trim()}
              onClick={handleAnalyze}
              style={{ marginBottom: '6px' }}
            >
              {loading ? (
                <>
                  <div className="loading-spinner"></div>
                  Diagnosing Nidana...
                </>
              ) : (
                <>
                  <span>🩺</span> Perform Differential Nidana
                </>
              )}
            </button>
            
            {/* Grouped Symptoms Category Selection */}
            <div className="symptoms-section">
              <h4 style={{ fontSize: '11px', color: 'var(--color-gold)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Quick Symptom Categorizer
              </h4>
              <div className="symptoms-category-box">
                {SYMPTOM_CATEGORIES.map((cat, cidx) => (
                  <div key={cidx} className="symptoms-cat-group">
                    <div className="symptoms-cat-title">{cat.category}</div>
                    <div className="chip-container">
                      {cat.symptoms.map((sym, sidx) => {
                        const isActive = caseText.toLowerCase().includes(sym.term.toLowerCase());
                        return (
                          <button
                            key={sidx}
                            className={`symptom-chip ${isActive ? 'active' : ''}`}
                            onClick={() => handleSymptomToggle(sym.term)}
                          >
                            {sym.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Center Column: Diagnostic Assistant Chatbot */}
        <section className="panel glass panel-chat">
          <div className="panel-header">
            <div className="panel-title">
              <span className="panel-title-icon">🏺</span>
              Madhava Diagnostic Consultation
            </div>
          </div>
          <div className="chat-container">
            <div className="chat-messages">
              {chatHistory.length === 0 ? (
                <div className="chat-welcome">
                  <div className="chat-welcome-icon">🏺</div>
                  <h2>Clinical Decision Support</h2>
                  <p>
                    Enter patient symptoms or select a classical case profile, then click <strong>Perform Differential Nidana</strong>. 
                    The clinical RAG assistant will cross-reference the symptoms with classical scriptures to formulate diagnostic proposals.
                  </p>
                </div>
              ) : (
                chatHistory.map((msg, idx) => (
                  <div key={idx} className={`message-bubble ${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'user' ? 'Clinical Practitioner' : 'Madhava RAG Specialist'}
                    </div>
                    <div className="message-content">
                      {msg.role === 'user' ? msg.content : renderMarkdown(msg.content)}
                    </div>
                  </div>
                ))
              )}
              {loading && chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'user' && (
                <div className="message-bubble assistant">
                  <div className="message-avatar">Madhava RAG Specialist</div>
                  <div className="loading-spinner" style={{ borderColor: 'var(--color-gold)', borderTopColor: 'transparent', width: '20px', height: '20px' }}></div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            
            <div className="chat-input-area">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask about specific symptoms, Samprapti (pathogenesis), or Pathya (diet)..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={chatHistory.length === 0 || loading}
              />
              <button
                className="btn-send"
                onClick={handleSendMessage}
                disabled={!chatMessage.trim() || chatHistory.length === 0 || loading}
              >
                ➔
              </button>
            </div>
          </div>
        </section>

        {/* Right Column: Reference Explorer & Diagnostic Matches */}
        <section className="panel glass panel-results">
          <div className="tabs-header">
            <button
              className={`tab-btn ${activeTab === 'diagnosis' ? 'active' : ''}`}
              onClick={() => { setActiveTab('diagnosis'); setSelectedChapter(null); }}
            >
              Differential Matches
            </button>
            <button
              className={`tab-btn ${activeTab === 'references' ? 'active' : ''}`}
              onClick={() => setActiveTab('references')}
            >
              Nidana Chapters
            </button>
          </div>
          
          <div className="tab-content">
            {activeTab === 'diagnosis' ? (
              searchResults.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#a3b899', padding: '40px 0', fontSize: '13px' }}>
                  No active diagnostic scans. Load a case profile to view matches.
                </div>
              ) : (
                searchResults.map((res, idx) => {
                  const d = res.disease;
                  return (
                    <div key={idx} className="diag-card animate-fade" style={{ animationDelay: `${idx * 0.08}s` }}>
                      <div className="diag-card-top">
                        <div className="diag-name">{d.roga}</div>
                        <div className="diag-score">{(res.score * 100).toFixed(0)}% Match</div>
                      </div>
                      
                      <div className="diag-metadata">
                        <div className="meta-item">Dosha: <span>{d.dosha.join(', ')}</span></div>
                        <div className="meta-item">Dushya: <span>{d.dushya.join(', ')}</span></div>
                        <div className="meta-item">Srotas: <span>{d.srotas.join(', ')}</span></div>
                        <div className="meta-item">Agni: <span>{d.agni ? d.agni : 'Mandagni'}</span></div>
                      </div>

                      {res.matched_symptoms.length > 0 && (
                        <div className="diag-symptoms">
                          {res.matched_symptoms.map((s, sidx) => (
                            <span key={sidx} className="matched-sym-chip">
                              ✓ {s.matched_term} ({s.ayurvedic_term})
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="diag-samprapti">
                        <strong>Samprapti:</strong> {d.samprapti}
                      </div>
                      
                      <div style={{ fontSize: '11px', color: '#a3b899', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(224, 159, 62, 0.05)', paddingTop: '8px' }}>
                        <span>Ref: {d.classical_references.join(', ')}</span>
                        <span>Sadhya: {d.sadhya_asadhyata}</span>
                      </div>
                    </div>
                  );
                })
              )
            ) : (
              // References Tab
              selectedChapter === null ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <p style={{ fontSize: '12px', color: '#a3b899', marginBottom: '8px' }}>
                    Browse classical Ayurvedic diagnostic chapters from <em>Madhava Nidana Volume 1</em>:
                  </p>
                  {chapters.map((ch) => (
                    <div
                      key={ch.chapter_number}
                      className="ref-chapter-item"
                      onClick={() => handleSelectChapter(ch.chapter_number)}
                    >
                      <div>
                        <div className="ref-chapter-name">Chapter {ch.chapter_number}: {ch.chapter_title}</div>
                        <div className="ref-chapter-meta">Pages {ch.start_page} - {ch.end_page} | {ch.chapter_type}</div>
                      </div>
                      <span style={{ color: 'var(--color-gold)' }}>➔</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div className="chapter-viewer-header">
                    <button className="btn-back-refs" onClick={() => setSelectedChapter(null)}>
                      ◀ Back to Chapters
                    </button>
                  </div>
                  <h3 style={{ fontSize: '16px', color: 'var(--color-gold)', fontFamily: 'var(--font-heading)' }}>
                    Chapter {selectedChapter}: {chapters.find(c => c.chapter_number === selectedChapter)?.chapter_title}
                  </h3>
                  {loadingChapter ? (
                    <div className="loading-container">
                      <div className="spinner"></div>
                      Loading chapter text...
                    </div>
                  ) : (
                    <div className="chapter-content-box">
                      {chapterContent}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        </section>
        
      </main>
    </div>
  );
}

export default App;
