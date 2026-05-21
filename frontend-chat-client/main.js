const els = Object.fromEntries([...document.querySelectorAll('[id]')].map((e) => [e.id, e]));

const state = {
  apiBaseUrl: localStorage.getItem('apiBaseUrl') || 'http://localhost:8000/api/v1',
  wsBaseUrl: localStorage.getItem('wsBaseUrl') || 'ws://localhost:8000/api/v1/chats/ws',
  accessToken: localStorage.getItem('accessToken') || '',
  activeChatId: null,
  ws: null,
};

function log(...args) {
  const line = `[${new Date().toISOString()}] ${args.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ')}`;
  els.logs.textContent = `${line}\n${els.logs.textContent}`;
}

function syncUi() {
  els.apiBaseUrl.value = state.apiBaseUrl;
  els.wsBaseUrl.value = state.wsBaseUrl;
  els.accessToken.value = state.accessToken;
  els.activeChatId.textContent = state.activeChatId || '-';
}

function saveState() {
  localStorage.setItem('apiBaseUrl', state.apiBaseUrl);
  localStorage.setItem('wsBaseUrl', state.wsBaseUrl);
  localStorage.setItem('accessToken', state.accessToken);
}

async function api(path, { method = 'GET', json, form, headers = {} } = {}) {
  const reqHeaders = { ...headers };
  let body;
  if (json) {
    reqHeaders['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  }
  if (form) {
    body = new URLSearchParams(form);
  }
  if (state.accessToken) reqHeaders.Authorization = `Bearer ${state.accessToken}`;

  const response = await fetch(`${state.apiBaseUrl}${path}`, {
    method,
    headers: reqHeaders,
    body,
    credentials: 'include',
  });
  const text = await response.text();
  let data = text;
  try { data = text ? JSON.parse(text) : null; } catch {}
  if (!response.ok) throw new Error(`${method} ${path} -> ${response.status}: ${JSON.stringify(data)}`);
  return data;
}

async function register() {
  const payload = {
    username: els.regUsername.value,
    email: els.regEmail.value,
    password: els.regPassword.value,
    password_repeat: els.regPasswordRepeat.value,
  };
  const data = await api('/users/register', { method: 'POST', json: payload });
  log('Registered:', data);
}

async function login() {
  const data = await api('/auth/login', {
    method: 'POST',
    form: { username: els.loginUsername.value, password: els.loginPassword.value },
  });
  state.accessToken = data.access_token;
  saveState();
  syncUi();
  log('Login ok, token set');
}

async function refresh() {
  const data = await api('/auth/refresh', { method: 'POST' });
  state.accessToken = data.access_token;
  saveState();
  syncUi();
  log('Token refreshed');
}

async function logout() {
  await api('/auth/logout', { method: 'POST' });
  state.accessToken = '';
  saveState();
  syncUi();
  log('Logout done');
}

async function loadMe() { log('me:', await api('/users/me')); }

async function loadChats() {
  const data = await api('/chats');
  const chats = data.items || data.chats || [];
  els.chatList.innerHTML = '';
  chats.forEach((chat) => {
    const li = document.createElement('li');
    li.textContent = `${chat.id} | ${chat.name || '(no name)'} | ${chat.type || ''}`;
    li.onclick = () => {
      state.activeChatId = chat.id;
      syncUi();
      log('Active chat:', chat.id);
    };
    els.chatList.appendChild(li);
  });
  log('Chats loaded:', chats.length);
}

async function createChat() {
  const data = await api('/chats', {
    method: 'POST',
    json: {
      name: els.chatName.value,
      description: els.chatDescription.value,
      chat_type: 'group',
      member_ids: [],
      is_public: false,
      admin_only: false,
      slow_mode_seconds: 0,
      permissions: {},
    },
  });
  state.activeChatId = data.id;
  syncUi();
  log('Chat created:', data);
}

async function loadMessages() {
  if (!state.activeChatId) throw new Error('Select chat first');
  const data = await api(`/chats/${state.activeChatId}/messages?limit=50`);
  const items = data.items || data.messages || [];
  els.messageList.innerHTML = '';
  items.forEach((m) => {
    const li = document.createElement('li');
    li.textContent = `#${m.seq} [${m.sender_id}] ${m.content || ''}`;
    els.messageList.appendChild(li);
  });
  log('Messages loaded:', items.length);
}

async function sendMessage() {
  if (!state.activeChatId) throw new Error('Select chat first');
  const data = await api(`/chats/${state.activeChatId}/messages`, {
    method: 'POST',
    json: { content: els.messageInput.value, message_type: 'text', upload_tokens: [] },
  });
  log('Message sent:', data);
  await loadMessages();
}

function connectWs() {
  if (!state.activeChatId) throw new Error('Select chat first');
  if (!state.accessToken) throw new Error('Login first');
  if (state.ws) state.ws.close();

  const url = `${state.wsBaseUrl}?token=${encodeURIComponent(state.accessToken)}`;
  const ws = new WebSocket(url, 'chat.v1');
  state.ws = ws;

  ws.onopen = () => {
    log('WS open');
    ws.send(JSON.stringify({ op: 'subscribe', chat_id: state.activeChatId, last_seq: 0 }));
    ws.send(JSON.stringify({ op: 'ping' }));
  };
  ws.onmessage = (event) => {
    log('WS event:', event.data);
    try {
      const parsed = JSON.parse(event.data);
      if (parsed.type?.includes('message')) loadMessages().catch((e) => log('loadMessages error', e.message));
    } catch {}
  };
  ws.onerror = (e) => log('WS error', e);
  ws.onclose = (e) => log(`WS close code=${e.code} reason=${e.reason}`);
}

els.saveConfigBtn.onclick = () => {
  state.apiBaseUrl = els.apiBaseUrl.value.trim();
  state.wsBaseUrl = els.wsBaseUrl.value.trim();
  saveState();
  log('Config saved');
};
els.registerBtn.onclick = () => register().catch((e) => log(e.message));
els.loginBtn.onclick = () => login().catch((e) => log(e.message));
els.refreshBtn.onclick = () => refresh().catch((e) => log(e.message));
els.logoutBtn.onclick = () => logout().catch((e) => log(e.message));
els.loadMeBtn.onclick = () => loadMe().catch((e) => log(e.message));
els.loadChatsBtn.onclick = () => loadChats().catch((e) => log(e.message));
els.createChatBtn.onclick = () => createChat().catch((e) => log(e.message));
els.loadMessagesBtn.onclick = () => loadMessages().catch((e) => log(e.message));
els.sendMessageBtn.onclick = () => sendMessage().catch((e) => log(e.message));
els.connectWsBtn.onclick = () => connectWs();

syncUi();
log('Client ready');
