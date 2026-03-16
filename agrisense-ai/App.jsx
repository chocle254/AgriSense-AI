import { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SAMPLE_QUESTIONS = [
  "My maize leaves are turning yellow from the tips — what's wrong?",
  "When should I plant beans this season?",
  "What is the current price of maize in Nairobi?",
  "How much fertiliser do I need for one acre?",
  "My tomatoes have dark spots on the fruit",
  "Where can I find certified seed near Eldoret?",
];

const AGENT_LABELS = {
  "crop-doctor": { label: "Crop Doctor", color: "#10b981", icon: "🔬" },
  "weather": { label: "Weather", color: "#3b82f6", icon: "🌤" },
  "market": { label: "Market", color: "#f59e0b", icon: "📊" },
  "agronomy": { label: "Agronomy", color: "#8b5cf6", icon: "🌱" },
  "input-finder": { label: "Suppliers", color: "#6366f1", icon: "🏪" },
  "orchestrator": { label: "Mama Shamba", color: "#ec4899", icon: "🌾" },
};

function AgentBadge({ agentUsed }) {
  const agent = AGENT_LABELS[agentUsed] || AGENT_LABELS["orchestrator"];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: "4px",
      fontSize: "11px", padding: "2px 8px", borderRadius: "12px",
      background: agent.color + "18", color: agent.color,
      border: `1px solid ${agent.color}30`, fontWeight: 500,
    }}>
      {agent.icon} {agent.label}
    </span>
  );
}

function SourceBadge({ sources }) {
  if (!sources?.length) return null;
  return (
    <div style={{ marginTop: "8px", fontSize: "11px", color: "#6b7280" }}>
      📚 {sources.length} knowledge source{sources.length > 1 ? "s" : ""} consulted
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex", flexDirection: isUser ? "row-reverse" : "row",
      gap: "10px", alignItems: "flex-start", marginBottom: "20px",
    }}>
      {!isUser && (
        <div style={{
          width: "36px", height: "36px", borderRadius: "50%", flexShrink: 0,
          background: "linear-gradient(135deg, #10b981, #059669)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "18px",
        }}>🌾</div>
      )}
      <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: "4px" }}>
        <div style={{
          padding: "12px 16px", borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
          background: isUser ? "#10b981" : "#f9fafb",
          color: isUser ? "#fff" : "#111827",
          fontSize: "14px", lineHeight: "1.6",
          border: isUser ? "none" : "1px solid #e5e7eb",
          whiteSpace: "pre-wrap",
        }}>
          {msg.content}
        </div>
        {!isUser && msg.agentUsed && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", paddingLeft: "4px" }}>
            <AgentBadge agentUsed={msg.agentUsed} />
            <SourceBadge sources={msg.sources} />
          </div>
        )}
      </div>
    </div>
  );
}

function PhotoUpload({ onClose, onDiagnosis }) {
  const [file, setFile] = useState(null);
  const [crop, setCrop] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    const form = new FormData();
    form.append("image", file);
    form.append("crop_name", crop || "unknown");
    form.append("symptoms", symptoms || "Please diagnose this crop photo");
    try {
      const resp = await fetch(`${API_BASE}/api/diagnose`, { method: "POST", body: form });
      const data = await resp.json();
      onDiagnosis(data.diagnosis || "Could not process image. Please describe symptoms in text.");
    } catch {
      onDiagnosis("Error connecting to diagnosis service. Please describe symptoms in text.");
    }
    setLoading(false);
    onClose();
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
    }}>
      <div style={{
        background: "#fff", borderRadius: "16px", padding: "24px",
        width: "min(480px, 90vw)", maxHeight: "80vh", overflow: "auto",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 600, margin: 0 }}>📸 Diagnose Crop Photo</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "20px", cursor: "pointer" }}>×</button>
        </div>

        <label style={{
          display: "block", border: "2px dashed #d1d5db", borderRadius: "12px",
          padding: "24px", textAlign: "center", cursor: "pointer", marginBottom: "16px",
        }}>
          {preview ? (
            <img src={preview} alt="preview" style={{ maxHeight: "200px", borderRadius: "8px" }} />
          ) : (
            <div>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>📷</div>
              <p style={{ color: "#6b7280", fontSize: "14px", margin: 0 }}>
                Click to upload crop photo
              </p>
            </div>
          )}
          <input type="file" accept="image/*" onChange={handleFile} style={{ display: "none" }} />
        </label>

        <input
          type="text" placeholder="Crop name (e.g. maize, beans, tomatoes)"
          value={crop} onChange={e => setCrop(e.target.value)}
          style={{
            width: "100%", padding: "10px 12px", borderRadius: "8px",
            border: "1px solid #d1d5db", fontSize: "14px", marginBottom: "10px",
            boxSizing: "border-box",
          }}
        />
        <textarea
          placeholder="Describe symptoms you can see..."
          value={symptoms} onChange={e => setSymptoms(e.target.value)}
          rows={3}
          style={{
            width: "100%", padding: "10px 12px", borderRadius: "8px",
            border: "1px solid #d1d5db", fontSize: "14px", resize: "vertical",
            marginBottom: "16px", boxSizing: "border-box",
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          style={{
            width: "100%", padding: "12px", borderRadius: "10px",
            background: file && !loading ? "#10b981" : "#d1d5db",
            color: "#fff", border: "none", fontSize: "15px", fontWeight: 600,
            cursor: file && !loading ? "pointer" : "not-allowed",
          }}
        >
          {loading ? "🔍 Diagnosing..." : "🔬 Diagnose Disease"}
        </button>
      </div>
    </div>
  );
}

export default function AgriSenseApp() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Habari! I'm Mama Shamba — your AI farming companion. 🌾\n\nI can help you with:\n• 🔬 Crop disease diagnosis (text or photo)\n• 🌤 Weather & planting advice\n• 📊 Market prices & sell timing\n• 🌱 Fertiliser & soil guidance\n• 🏪 Finding agro-dealers near you\n\nWhat can I help you grow today?",
      agentUsed: "orchestrator",
      sources: [],
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPhoto, setShowPhoto] = useState(false);
  const [language, setLanguage] = useState("auto");
  const [stats, setStats] = useState({ queries: 0, diseases: 0, farmers: "500M+" });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    const userMsg = { role: "user", content: messageText };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageText,
          farmer_id: "web-user",
          channel: "web",
          language,
          conversation_history: history,
        }),
      });

      if (!resp.ok) throw new Error("API error");
      const data = await resp.json();

      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.response,
        agentUsed: data.agent_used,
        sources: data.sources,
      }]);
      setStats(s => ({ ...s, queries: s.queries + 1 }));
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I'm having trouble connecting right now. Please try again in a moment, or send an SMS to our shortcode for offline access.",
        agentUsed: "orchestrator",
        sources: [],
      }]);
    }
    setLoading(false);
    inputRef.current?.focus();
  };

  const handlePhotoDiagnosis = (diagnosis) => {
    setMessages(prev => [...prev, {
      role: "assistant",
      content: diagnosis,
      agentUsed: "crop-doctor",
      sources: ["Crop Disease Knowledge Base"],
    }]);
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "system-ui, sans-serif", background: "#f0fdf4" }}>
      
      {/* Sidebar */}
      <div style={{
        width: "280px", background: "#fff", borderRight: "1px solid #e5e7eb",
        display: "flex", flexDirection: "column", flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: "20px", borderBottom: "1px solid #e5e7eb" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "40px", height: "40px", background: "linear-gradient(135deg, #10b981, #059669)",
              borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "20px",
            }}>🌾</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "16px", color: "#064e3b" }}>AgriSense AI</div>
              <div style={{ fontSize: "11px", color: "#6b7280" }}>Powered by Gradient™ AI</div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div style={{ padding: "16px", borderBottom: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6b7280", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Platform stats</div>
          {[
            { label: "Farmers served", value: stats["farmers"] },
            { label: "Crops covered", value: "120+" },
            { label: "Diseases in database", value: "2,000+" },
            { label: "Languages", value: "EN · SW · FR · HA" },
          ].map(s => (
            <div key={s.label} style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span style={{ fontSize: "12px", color: "#6b7280" }}>{s.label}</span>
              <span style={{ fontSize: "12px", fontWeight: 600, color: "#064e3b" }}>{s.value}</span>
            </div>
          ))}
        </div>

        {/* Agents */}
        <div style={{ padding: "16px", borderBottom: "1px solid #e5e7eb" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6b7280", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Specialist agents</div>
          {Object.entries(AGENT_LABELS).filter(([k]) => k !== "orchestrator").map(([key, agent]) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <span style={{ fontSize: "14px" }}>{agent.icon}</span>
              <span style={{ fontSize: "12px", color: "#374151" }}>{agent.label}</span>
              <div style={{ marginLeft: "auto", width: "6px", height: "6px", borderRadius: "50%", background: agent.color }} />
            </div>
          ))}
        </div>

        {/* Language selector */}
        <div style={{ padding: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#6b7280", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Response language</div>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            style={{
              width: "100%", padding: "8px 10px", borderRadius: "8px",
              border: "1px solid #d1d5db", fontSize: "13px", background: "#fff",
            }}
          >
            <option value="auto">Auto-detect</option>
            <option value="en">English</option>
            <option value="sw">Kiswahili</option>
            <option value="fr">Français</option>
            <option value="ha">Hausa</option>
          </select>
        </div>

        {/* SMS info */}
        <div style={{
          margin: "0 16px 16px", padding: "12px", background: "#f0fdf4",
          borderRadius: "10px", border: "1px solid #a7f3d0", marginTop: "auto",
        }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#065f46", marginBottom: "4px" }}>📱 No smartphone?</div>
          <div style={{ fontSize: "11px", color: "#047857" }}>SMS *384# from any phone for offline access across 35 African countries.</div>
        </div>
      </div>

      {/* Main chat */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        
        {/* Header */}
        <div style={{
          padding: "14px 20px", background: "#fff", borderBottom: "1px solid #e5e7eb",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: "15px" }}>Chat with Mama Shamba</div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>Multi-agent agricultural AI · DigitalOcean Gradient™ AI</div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => setShowPhoto(true)}
              style={{
                padding: "8px 14px", borderRadius: "8px", border: "1px solid #d1d5db",
                background: "#fff", fontSize: "13px", cursor: "pointer",
                display: "flex", alignItems: "center", gap: "6px",
              }}
            >
              📸 Diagnose photo
            </button>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          {loading && (
            <div style={{ display: "flex", gap: "10px", alignItems: "flex-start", marginBottom: "20px" }}>
              <div style={{
                width: "36px", height: "36px", borderRadius: "50%", flexShrink: 0,
                background: "linear-gradient(135deg, #10b981, #059669)",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px",
              }}>🌾</div>
              <div style={{
                padding: "12px 16px", borderRadius: "4px 16px 16px 16px",
                background: "#f9fafb", border: "1px solid #e5e7eb",
                display: "flex", gap: "4px", alignItems: "center",
              }}>
                {[0,1,2].map(i => (
                  <div key={i} style={{
                    width: "6px", height: "6px", borderRadius: "50%", background: "#10b981",
                    animation: `bounce 1.2s ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick prompts */}
        {messages.length <= 1 && (
          <div style={{ padding: "0 20px 12px", display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {SAMPLE_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                style={{
                  padding: "7px 12px", borderRadius: "20px",
                  border: "1px solid #a7f3d0", background: "#f0fdf4",
                  fontSize: "12px", color: "#065f46", cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input area */}
        <div style={{
          padding: "14px 20px", background: "#fff", borderTop: "1px solid #e5e7eb",
          display: "flex", gap: "10px", alignItems: "flex-end",
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }}}
            placeholder="Ask Mama Shamba anything about your farm..."
            rows={1}
            style={{
              flex: 1, padding: "12px 14px", borderRadius: "12px",
              border: "1px solid #d1d5db", fontSize: "14px", resize: "none",
              outline: "none", fontFamily: "inherit", lineHeight: "1.5",
              maxHeight: "120px", overflow: "auto",
            }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            style={{
              width: "44px", height: "44px", borderRadius: "12px",
              background: input.trim() && !loading ? "#10b981" : "#d1d5db",
              border: "none", color: "#fff", fontSize: "18px",
              cursor: input.trim() && !loading ? "pointer" : "not-allowed",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}
          >
            ↑
          </button>
        </div>
      </div>

      {showPhoto && (
        <PhotoUpload
          onClose={() => setShowPhoto(false)}
          onDiagnosis={handlePhotoDiagnosis}
        />
      )}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        * { box-sizing: border-box; }
        body { margin: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
      `}</style>
    </div>
  );
}
