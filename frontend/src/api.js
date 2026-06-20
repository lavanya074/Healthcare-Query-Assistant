const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

async function postJSON(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.error || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function sendMessage(message, sessionId) {
  return postJSON("/api/chat", { message, session_id: sessionId });
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error("Backend unreachable");
  return response.json();
}
