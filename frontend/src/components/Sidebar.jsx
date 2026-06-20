import React from "react";

// Real categories pulled from the knowledge base — these double as
// quick-start prompts, so the structure encodes actual content, not
// decoration.
const CATEGORIES = [
  { label: "Insurance & Claims", prompt: "How do I check the status of my insurance claim?" },
  { label: "Prescriptions", prompt: "How do I refill a prescription through mail order?" },
  { label: "Benefits & Coverage", prompt: "What is a deductible and how does it work?" },
  { label: "Telehealth", prompt: "How do I schedule a telehealth appointment?" },
  { label: "Wellness Programs", prompt: "How do I enroll in a wellness program?" },
  { label: "Account & Access", prompt: "How do I reset my member portal password?" },
];

function PulseDivider() {
  return (
    <svg className="pulse-divider" viewBox="0 0 240 22" preserveAspectRatio="none">
      <path d="M0 11 H70 L80 2 L92 20 L104 6 L114 11 H240" />
    </svg>
  );
}

export default function Sidebar({ onPromptSelect, backendStatus }) {
  return (
    <aside className="sidebar">
      <div>
        <div className="sidebar-brand">Healthcare Query Assistant</div>
        <div className="sidebar-tagline">Answers grounded in your plan's knowledge base.</div>
      </div>

      <PulseDivider />

      <div>
        <div className="sidebar-section-label">Browse topics</div>
        <ul className="category-list">
          {CATEGORIES.map((cat) => (
            <li key={cat.label}>
              <button className="category-button" onClick={() => onPromptSelect(cat.prompt)}>
                {cat.label}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="sidebar-footer">
        <span
          className={`status-dot ${backendStatus === "online" ? "online" : "offline"}`}
        />
        {backendStatus === "online" ? "Connected to backend" : "Backend unreachable"}
        <br />
        Retrieval-Augmented Generation · FAISS + Hugging Face embeddings
      </div>
    </aside>
  );
}
