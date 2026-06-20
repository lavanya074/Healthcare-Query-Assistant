import React, { useState } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <form className="chat-input-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask about claims, prescriptions, benefits, telehealth…"
        disabled={disabled}
        aria-label="Type your question"
      />
      <button type="submit" className="send-button" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
