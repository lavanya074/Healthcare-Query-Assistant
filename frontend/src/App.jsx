import React, { useEffect, useRef, useState } from "react";
import "./styles.css";
import Sidebar from "./components/Sidebar";
import MessageBubble from "./components/MessageBubble";
import ChatInput from "./components/ChatInput";
import { sendMessage, checkHealth } from "./api";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  const scrollRef = useRef(null);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const handleSend = async (text) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setIsSending(true);

    try {
      const data = await sendMessage(text, sessionId);
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Something went wrong reaching the assistant. Confirm the backend is running on the configured API URL and try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="app-shell">
      <Sidebar onPromptSelect={handleSend} backendStatus={backendStatus} />

      <div className="chat-column">
        <header className="chat-header">
          <h1>Plan Benefits Assistant</h1>
          <p>Retrieval-grounded answers — not medical advice.</p>
        </header>

        <div className="chat-window">
          {messages.length === 0 && (
            <div className="empty-state">
              <h2>Ask a question to get started</h2>
              <p>
                Try a topic from the sidebar, or ask in your own words —
                e.g. "What's the difference between a copay and coinsurance?"
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageBubble key={idx} role={msg.role} content={msg.content} sources={msg.sources} />
          ))}

          {isSending && <MessageBubble role="assistant" loading />}

          <div ref={scrollRef} />
        </div>

        <ChatInput onSend={handleSend} disabled={isSending} />
        <div className="disclaimer">
          This assistant answers benefits, claims, and plan questions only. It does not provide medical diagnoses or treatment advice.
        </div>
      </div>
    </div>
  );
}
