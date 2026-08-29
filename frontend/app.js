/**
 * khaoAI — Client-side chat application
 *
 * WebSocket-based chat with streaming tokens, food recommendation cards,
 * auth flow, settings, and graph-trace display.
 */

// ─── State ───────────────────────────────────────────────────────────
const state = {
  token: localStorage.getItem('khaoai_token') || null,
  user: JSON.parse(localStorage.getItem('khaoai_user') || 'null'),
  sessionId: 'sess-' + Math.random().toString(36).substring(2, 9),
  ws: null,
  isStreaming: false,
  settings: JSON.parse(localStorage.getItem('khaoai_settings') || 'null') || {
    default_location: 'Salt Lake, Sector V',
    dietary_preference: 'all',
    budget_preference: 'medium',
    max_delivery_time: 45,
  },
};


// ─── DOM References ──────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const authPage      = $('#auth-page');
const appPage       = $('#app-page');
const authForm      = $('#auth-form');
const authTitle     = $('#auth-title');
const authEmail     = $('#auth-email');
const authPassword  = $('#auth-password');
const authName      = $('#auth-name');
const authNameWrap  = $('#auth-name-wrap');
const authError     = $('#auth-error');
const authSubmit    = $('#auth-submit');
const authToggleText = $('#auth-toggle-text');
const authToggleLink = $('#auth-toggle-link');
const welcomeScreen = $('#welcome-screen');
const messagesDiv   = $('#messages');
const chatForm      = $('#chat-form');
const chatInput     = $('#chat-input');
const chatSend      = $('#chat-send');
const settingsModal = $('#settings-modal');

let isRegisterMode = false;


// ─── Auth ────────────────────────────────────────────────────────────
function showAuth() {
  authPage.style.display = 'flex';
  appPage.style.display = 'none';
}

function showApp() {
  authPage.style.display = 'none';
  appPage.style.display = 'flex';
  connectWebSocket();
}

authToggleLink.addEventListener('click', (e) => {
  e.preventDefault();
  isRegisterMode = !isRegisterMode;
  if (isRegisterMode) {
    authTitle.textContent = 'Create Account';
    authSubmit.textContent = 'Register';
    authToggleText.textContent = 'Already have an account?';
    authToggleLink.textContent = 'Sign In';
    authNameWrap.style.display = 'block';
  } else {
    authTitle.textContent = 'Sign in to khaoAI';
    authSubmit.textContent = 'Sign In';
    authToggleText.textContent = "Don't have an account?";
    authToggleLink.textContent = 'Register';
    authNameWrap.style.display = 'none';
  }
  authError.textContent = '';
});

authForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  authError.textContent = '';
  const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
  const body = { email: authEmail.value, password: authPassword.value };
  if (isRegisterMode) body.display_name = authName.value || 'Foodie';

  try {
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Auth failed');

    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem('khaoai_token', data.access_token);
    localStorage.setItem('khaoai_user', JSON.stringify(data.user));
    showApp();
  } catch (err) {
    authError.textContent = err.message;
  }
});

$('#btn-logout').addEventListener('click', () => {
  state.token = null;
  state.user = null;
  localStorage.removeItem('khaoai_token');
  localStorage.removeItem('khaoai_user');
  if (state.ws) { state.ws.close(); state.ws = null; }
  messagesDiv.innerHTML = '';
  welcomeScreen.style.display = 'flex';
  showAuth();
});


// ─── Settings ────────────────────────────────────────────────────────
$('#btn-settings').addEventListener('click', () => {
  $('#set-location').value = state.settings.default_location;
  $('#set-diet').value = state.settings.dietary_preference;
  $('#set-budget').value = state.settings.budget_preference;
  $('#set-delivery').value = String(state.settings.max_delivery_time);
  settingsModal.style.display = 'flex';
});

$('#settings-close').addEventListener('click', () => {
  settingsModal.style.display = 'none';
});

settingsModal.addEventListener('click', (e) => {
  if (e.target === settingsModal) settingsModal.style.display = 'none';
});

$('#settings-save').addEventListener('click', () => {
  state.settings = {
    default_location: $('#set-location').value,
    dietary_preference: $('#set-diet').value,
    budget_preference: $('#set-budget').value,
    max_delivery_time: parseInt($('#set-delivery').value, 10),
  };
  localStorage.setItem('khaoai_settings', JSON.stringify(state.settings));
  settingsModal.style.display = 'none';
});


// ─── New Chat ────────────────────────────────────────────────────────
$('#btn-new-chat').addEventListener('click', () => {
  state.sessionId = 'sess-' + Math.random().toString(36).substring(2, 9);
  messagesDiv.innerHTML = '';
  welcomeScreen.style.display = 'flex';
  if (state.ws) { state.ws.close(); state.ws = null; }
  connectWebSocket();
});


// ─── Quick Chips ─────────────────────────────────────────────────────
document.querySelectorAll('.chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    const prompt = chip.dataset.prompt;
    if (prompt) sendMessage(prompt);
  });
});


// ─── WebSocket ───────────────────────────────────────────────────────
function connectWebSocket() {
  if (state.ws && state.ws.readyState <= 1) return;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  let url = `${proto}//${location.host}/api/chat/ws/${state.sessionId}`;
  if (state.token) url += `?token=${encodeURIComponent(state.token)}`;

  state.ws = new WebSocket(url);
  let streamingEl = null;
  let streamedText = '';

  state.ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'status') {
      removeStatus();
      appendStatus(msg.content);
    }

    if (msg.type === 'token') {
      removeStatus();
      if (!streamingEl) {
        welcomeScreen.style.display = 'none';
        streamingEl = appendAssistantStreaming();
        streamedText = '';
        state.isStreaming = true;
        updateSendButton();
      }
      streamedText += msg.content;
      streamingEl.querySelector('.msg-reply').innerHTML = formatMarkdown(streamedText) + '<span class="streaming-cursor"></span>';
      scrollToBottom();
    }

    if (msg.type === 'complete') {
      removeStatus();
      state.isStreaming = false;
      updateSendButton();

      if (streamingEl) {
        streamingEl.querySelector('.msg-reply').innerHTML = formatMarkdown(msg.reply || streamedText);
        // Add food cards
        if (msg.recommendations && msg.recommendations.length > 0) {
          streamingEl.appendChild(buildFoodCards(msg.recommendations));
        }
        // Add graph trace
        if (msg.graph_trace) {
          streamingEl.appendChild(buildTraceToggle(msg.graph_trace));
        }
        streamingEl = null;
        streamedText = '';
      } else {
        // No streaming happened (edge case)
        welcomeScreen.style.display = 'none';
        const el = appendAssistantMessage(msg.reply || '');
        if (msg.recommendations && msg.recommendations.length > 0) {
          el.appendChild(buildFoodCards(msg.recommendations));
        }
        if (msg.graph_trace) {
          el.appendChild(buildTraceToggle(msg.graph_trace));
        }
      }
      scrollToBottom();
    }
  };

  state.ws.onclose = () => {
    state.isStreaming = false;
    updateSendButton();
  };
}


// ─── Send Message ────────────────────────────────────────────────────
function sendMessage(text) {
  if (!text.trim() || state.isStreaming) return;
  if (!state.ws || state.ws.readyState !== 1) connectWebSocket();

  welcomeScreen.style.display = 'none';
  appendUserMessage(text);

  state.ws.send(JSON.stringify({
    message: text,
    location: state.settings.default_location,
    preferences: state.settings,
  }));

  chatInput.value = '';
  updateSendButton();
  scrollToBottom();
}

chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  sendMessage(chatInput.value);
});

chatInput.addEventListener('input', updateSendButton);

function updateSendButton() {
  chatSend.disabled = !chatInput.value.trim() || state.isStreaming;
}


// ─── DOM Builders ────────────────────────────────────────────────────
function appendUserMessage(text) {
  const el = document.createElement('div');
  el.className = 'msg msg-user';
  el.textContent = text;
  messagesDiv.appendChild(el);
}

function appendAssistantMessage(text) {
  const el = document.createElement('div');
  el.className = 'msg msg-assistant';
  el.innerHTML = `<div class="msg-reply">${formatMarkdown(text)}</div>`;
  messagesDiv.appendChild(el);
  return el;
}

function appendAssistantStreaming() {
  const el = document.createElement('div');
  el.className = 'msg msg-assistant';
  el.innerHTML = '<div class="msg-reply"><span class="streaming-cursor"></span></div>';
  messagesDiv.appendChild(el);
  return el;
}

function appendStatus(text) {
  const el = document.createElement('div');
  el.className = 'msg-status';
  el.id = 'current-status';
  el.innerHTML = `<span class="status-dot"></span>${text}`;
  messagesDiv.appendChild(el);
  scrollToBottom();
}

function removeStatus() {
  const el = document.getElementById('current-status');
  if (el) el.remove();
}


// ─── Food Cards ──────────────────────────────────────────────────────
function buildFoodCards(items) {
  const grid = document.createElement('div');
  grid.className = 'food-cards';
  items.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'food-card';

    const platformClass = item.platform?.toLowerCase() === 'tomato' ? 'tomato' : 'twiggy';
    const platformLabel = item.platform?.toLowerCase() === 'tomato' ? '🍅 Tomato' : '🌿 Twiggy';

    let badgesHtml = '';
    if (item.badges && item.badges.length > 0) {
      badgesHtml = '<div class="food-card-badges">' +
        item.badges.map((b) => {
          let cls = 'badge ';
          if (b.includes('Cheapest')) cls += 'badge-cheapest';
          else if (b.includes('Top')) cls += 'badge-toprated';
          else if (b.includes('Superfast') || b.includes('Fast')) cls += 'badge-fast';
          return `<span class="${cls}">${b}</span>`;
        }).join('') +
        '</div>';
    }

    const vegIcon = item.is_veg ? '🟢' : '🔴';

    card.innerHTML = `
      <div class="food-card-header">
        <span class="food-card-name">${vegIcon} ${escHtml(item.name)}</span>
        <span class="food-card-platform ${platformClass}">${platformLabel}</span>
      </div>
      <div class="food-card-restaurant">${escHtml(item.restaurant_name)}</div>
      <div class="food-card-meta">
        <span class="food-card-price">₹${item.price}</span>
        <span class="food-card-rating">⭐ ${item.rating}</span>
        <span>🕐 ${item.delivery_time_mins} min</span>
      </div>
      ${badgesHtml}
    `;
    grid.appendChild(card);
  });
  return grid;
}


// ─── Graph Trace ─────────────────────────────────────────────────────
function buildTraceToggle(trace) {
  const wrap = document.createElement('div');

  const btn = document.createElement('button');
  btn.className = 'trace-toggle';
  btn.innerHTML = `⚙ Graph trace (${Math.round(trace.total_duration_ms)}ms) ▸`;

  const panel = document.createElement('div');
  panel.className = 'trace-panel';
  panel.style.display = 'none';

  const pathStr = (trace.path || []).join(' → ');
  let stepsHtml = (trace.steps || []).map((s) => {
    const status = s.error ? '✗' : '✓';
    const summary = Object.entries(s.output_summary || {}).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ');
    return `<span class="trace-node">${s.node}</span> ${status} <span class="trace-time">${Math.round(s.duration_ms)}ms</span>  ${summary}`;
  }).join('\n');

  panel.innerHTML = `<span class="trace-path">Path: ${pathStr}</span>\n<span class="trace-time">Total: ${Math.round(trace.total_duration_ms)}ms</span>\n\n${stepsHtml}`;

  btn.addEventListener('click', () => {
    const open = panel.style.display !== 'none';
    panel.style.display = open ? 'none' : 'block';
    btn.innerHTML = `⚙ Graph trace (${Math.round(trace.total_duration_ms)}ms) ${open ? '▸' : '▾'}`;
  });

  wrap.appendChild(btn);
  wrap.appendChild(panel);
  return wrap;
}


// ─── Utilities ───────────────────────────────────────────────────────
function scrollToBottom() {
  const area = document.getElementById('chat-area');
  requestAnimationFrame(() => { area.scrollTop = area.scrollHeight; });
}

function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');
}


// ─── Init ────────────────────────────────────────────────────────────
if (state.token && state.user) {
  showApp();
} else {
  showAuth();
}
