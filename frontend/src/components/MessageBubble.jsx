import React from "react";

export default function MessageBubble({ role, content, sources, loading }) {
  return (
    <div className={`message-row ${role}`}>
      <div className={`bubble ${role} ${loading ? "loading" : ""}`}>
        {loading ? "Thinking…" : content}

        {!loading && sources && sources.length > 0 && (
          <div className="sources">
            {sources.map((source) => (
              <span key={source.id} className="source-chip" title={source.question}>
                {source.category} · {Math.round(source.score * 100)}%
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
