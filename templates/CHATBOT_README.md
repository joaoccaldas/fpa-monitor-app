# Universal Chatbot Integration Guide (PingPong)

This guide documents how the Universal Chatbot is integrated into the FP&A dashboard and how to configure and use it.

## Backend

A new endpoint `/chatbot` is available in `app.py`.
- Provider-agnostic: supports Perplexity, OpenAI-compatible (incl. Ollama) via the `openai` Python SDK.
- Keeps lightweight in-memory message history per `session_id` (last 10 turns). For production, use Redis/DB.

Environment variables (set in deployment):
- `LLM_PROVIDER`: `perplexity` (default) | `ollama` | `openai`
- `LLM_API_KEY`: API key for provider (not required for local Ollama)
- `LLM_BASE_URL`: Base URL for API (e.g., `https://api.perplexity.ai` or `http://localhost:11434/v1` for Ollama)
- `LLM_MODEL`: Default `llama-3.1-sonar-small-128k-online` (Perplexity), or your model name (e.g., `gpt-4o-mini`, `llama3:latest`)

Request example:
```
POST /chatbot
{
  "message": "What is EBITDA?",
  "session_id": "user-123"
}
```
Response example:
```
{
  "reply": "EBITDA stands for ...",
  "session_id": "user-123"
}
```

Clear history:
```
POST /chatbot/clear
{
  "session_id": "user-123"
}
```

## Frontend (index.html)

Add a business-styled chat widget to the dashboard (floating button + panel):

1) Add styles (inside <head>):
```html
<style>
.chatbot-toggle { position: fixed; right: 20px; bottom: 20px; z-index: 1050; }
.chatbot-panel { position: fixed; right: 20px; bottom: 90px; width: 360px; max-height: 520px; z-index: 1050; display: none; }
.chatbot-card { border: 1px solid #e9ecef; border-radius: .75rem; box-shadow: 0 .5rem 1rem rgba(0,0,0,.15); }
.chatbot-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
.chatbot-messages { height: 320px; overflow-y: auto; background: #fafbff; padding: .75rem; }
.msg { padding: .5rem .75rem; border-radius: .5rem; margin-bottom: .5rem; max-width: 85%; }
.msg-user { background: #e7f1ff; color: #0b5ed7; margin-left: auto; }
.msg-bot { background: #fff; border: 1px solid #edf2f7; color: #334155; }
</style>
```

2) Add widget markup (near end of <body>):
```html
<button id="chatbotToggle" class="btn btn-primary rounded-circle p-3 chatbot-toggle" title="Chat with PingPong">
  <i class="bi bi-chat-dots" style="font-size:1.25rem"></i>
</button>
<div id="chatbotPanel" class="chatbot-panel">
  <div class="card chatbot-card">
    <div class="card-header d-flex justify-content-between align-items-center chatbot-header">
      <span class="fw-semibold">PingPong AI</span>
      <div class="d-flex gap-2">
        <button id="chatClear" class="btn btn-sm btn-light text-primary">Clear</button>
        <button id="chatClose" class="btn btn-sm btn-light">✕</button>
      </div>
    </div>
    <div id="chatMessages" class="chatbot-messages"></div>
    <div class="card-footer">
      <div class="input-group">
        <input id="chatInput" type="text" class="form-control" placeholder="Ask anything..."/>
        <button id="chatSend" class="btn btn-primary"><i class="bi bi-send"></i></button>
      </div>
      <div class="small text-muted mt-1">Powered by configurable LLM backend</div>
    </div>
  </div>
</div>
```

3) Add script (after existing scripts):
```html
<script>
(function(){
  const apiBase = '';
  const sesIdKey = 'pp_chat_session_id';
  function getSessionId(){
    let s = localStorage.getItem(sesIdKey);
    if (!s) { s = 'sess-' + Math.random().toString(36).slice(2); localStorage.setItem(sesIdKey, s); }
    return s;
  }
  const elToggle = document.getElementById('chatbotToggle');
  const elPanel = document.getElementById('chatbotPanel');
  const elClose = document.getElementById('chatClose');
  const elClear = document.getElementById('chatClear');
  const elMsgs = document.getElementById('chatMessages');
  const elInput = document.getElementById('chatInput');
  const elSend = document.getElementById('chatSend');

  function appendMsg(content, who='bot'){
    const div = document.createElement('div');
    div.className = 'msg ' + (who==='user' ? 'msg-user' : 'msg-bot');
    div.textContent = content;
    elMsgs.appendChild(div);
    elMsgs.scrollTop = elMsgs.scrollHeight;
  }

  async function send(){
    const text = (elInput.value || '').trim();
    if (!text) return;
    appendMsg(text, 'user');
    elInput.value = '';
    try {
      const res = await fetch(`${apiBase}/chatbot`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: getSessionId() }) });
      const json = await res.json();
      const reply = json && (json.reply || json.error || 'No response');
      appendMsg(reply, 'bot');
    } catch(e) {
      appendMsg('Error: ' + (e.message || e.toString()), 'bot');
    }
  }

  elSend.addEventListener('click', send);
  elInput.addEventListener('keydown', (e)=>{ if (e.key === 'Enter') { send(); } });
  elToggle.addEventListener('click', ()=>{ elPanel.style.display = (elPanel.style.display==='block' ? 'none' : 'block'); });
  elClose.addEventListener('click', ()=>{ elPanel.style.display = 'none'; });
  elClear.addEventListener('click', async ()=>{
    try { await fetch(`${apiBase}/chatbot/clear`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: getSessionId() }) }); elMsgs.innerHTML = ''; }
    catch(e) { /* ignore */ }
  });
})();
</script>
```

Notes:
- `apiBase` is empty for same-origin backend. If using a reverse proxy, set accordingly.
- Uses localStorage to persist `session_id` across reloads (basic persistence). For server-side persistence, wire to a DB.
- Business styling with Bootstrap; responsive and compact.

## Deployment

1. Ensure `requirements.txt` includes `openai>=1.12.0` (already added).
2. Configure env vars on the platform (Render, Railway, Fly.io, Heroku, etc.). Example (Perplexity):
   - `LLM_PROVIDER=perplexity`
   - `LLM_API_KEY=pxy-...`
   - `LLM_BASE_URL=https://api.perplexity.ai`
   - `LLM_MODEL=llama-3.1-sonar-small-128k-online`
3. Deploy as usual (Gunicorn command example): `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`.
4. Verify endpoint: `curl -X POST "$HOST/chatbot" -H 'Content-Type: application/json' -d '{"message":"Hello"}'`.

## Testing
- Basic ping: send any message and confirm a textual reply.
- Finance context: ask about budgeting, forecasting, cash flow; expect actionable, concise advice.
- Data context: upload a file, then ask questions; bot mentions dataset shape/columns if available.

## Commit Message
Use: `Feature: Universal chatbot with FP&A + general chat capability.`

## Changelog
- Added `/chatbot` and `/chatbot/clear` endpoints
- In-memory session history with `session_id`
- Frontend widget spec (button, panel, styles, JS) for business use
