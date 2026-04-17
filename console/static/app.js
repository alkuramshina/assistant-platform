const state = {
  bots: [],
  selectedId: null,
};

const endpoints = {
  bots: "/api/bots",
  logs: (id) => `/api/bots/${id}/logs`,
  start: (id) => `/api/bots/${id}/start`,
  stop: (id) => `/api/bots/${id}/stop`,
};

const els = {
  form: document.querySelector("#bot-form"),
  refresh: document.querySelector("#refresh"),
  bots: document.querySelector("#bots"),
  botCount: document.querySelector("#bot-count"),
  selectedName: document.querySelector("#selected-name"),
  selectedStatus: document.querySelector("#selected-status"),
  details: document.querySelector("#bot-details"),
  start: document.querySelector("#start"),
  stop: document.querySelector("#stop"),
  message: document.querySelector("#message"),
  reloadLogs: document.querySelector("#reload-logs"),
  logs: document.querySelector("#logs"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function setMessage(text, kind = "") {
  els.message.textContent = text;
  els.message.dataset.kind = kind;
}

function selectedBot() {
  return state.bots.find((bot) => bot.id === state.selectedId) || null;
}

function renderBots() {
  els.botCount.textContent = String(state.bots.length);
  els.bots.innerHTML = "";

  if (state.bots.length === 0) {
    els.bots.innerHTML = '<p class="empty">No bots yet.</p>';
    renderSelected();
    return;
  }

  state.bots.forEach((bot) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "bot-item";
    button.dataset.active = bot.id === state.selectedId ? "true" : "false";
    button.innerHTML = `
      <span>${escapeHtml(bot.name)}</span>
      <small>${escapeHtml(bot.status)}</small>
    `;
    button.addEventListener("click", () => selectBot(bot.id));
    els.bots.append(button);
  });
  renderSelected();
}

function renderSelected() {
  const bot = selectedBot();
  if (!bot) {
    els.selectedName.textContent = "Select a bot";
    els.selectedStatus.textContent = "idle";
    els.details.innerHTML = "";
    els.start.disabled = true;
    els.stop.disabled = true;
    els.reloadLogs.disabled = true;
    els.logs.innerHTML = '<p class="empty">Select a bot to view Activity.</p>';
    return;
  }

  els.selectedName.textContent = bot.name;
  els.selectedStatus.textContent = bot.status;
  els.start.disabled = bot.status === "running";
  els.stop.disabled = bot.status !== "running";
  els.reloadLogs.disabled = false;
  els.details.innerHTML = `
    <dt>ID</dt><dd>${escapeHtml(bot.id)}</dd>
    <dt>Allowed users</dt><dd>${escapeHtml(bot.allowed_user_ids || "not set")}</dd>
    <dt>Provider</dt><dd>${escapeHtml(bot.provider_base_url || "not set")}</dd>
    <dt>Model</dt><dd>${escapeHtml(bot.provider_model || "not set")}</dd>
    <dt>Telegram token secret</dt><dd>${escapeHtml(bot.channel_secret_ref || "not set")}</dd>
    <dt>Provider key secret</dt><dd>${escapeHtml(bot.provider_secret_ref || "not set")}</dd>
  `;
}

function renderLogs(logs) {
  els.logs.innerHTML = "";
  if (logs.length === 0) {
    els.logs.innerHTML = '<p class="empty">No Activity yet.</p>';
    return;
  }

  logs.forEach((log) => {
    const item = document.createElement("article");
    item.className = "log-item";
    const time = new Date(log.created_at * 1000).toLocaleString();
    item.innerHTML = `
      <div><strong>${escapeHtml(log.status)}</strong><time>${escapeHtml(time)}</time></div>
      <p><b>User ${escapeHtml(log.telegram_user_id || "-")}</b>: ${escapeHtml(log.user_request || "")}</p>
      <p><b>Bot</b>: ${escapeHtml(log.assistant_response || "")}</p>
      ${log.error ? `<p class="error">${escapeHtml(log.error)}</p>` : ""}
    `;
    els.logs.append(item);
  });
}

async function loadBots() {
  const payload = await api(endpoints.bots);
  state.bots = payload.bots || [];
  if (state.selectedId && !state.bots.some((bot) => bot.id === state.selectedId)) {
    state.selectedId = null;
  }
  renderBots();
}

async function selectBot(id) {
  state.selectedId = id;
  renderBots();
  await loadLogs();
}

async function loadLogs() {
  if (!state.selectedId) {
    return;
  }
  const payload = await api(endpoints.logs(state.selectedId));
  renderLogs(payload.logs || []);
}

async function createBot(event) {
  event.preventDefault();
  const form = new FormData(els.form);
  const payload = Object.fromEntries(form.entries());
  try {
    const created = await api(endpoints.bots, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    els.form.reset();
    state.selectedId = created.bot.id;
    await loadBots();
    await loadLogs();
    setMessage("Bot created.", "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

async function runAction(action) {
  const bot = selectedBot();
  if (!bot) {
    return;
  }
  try {
    const payload = await api(endpoints[action](bot.id), {
      method: "POST",
      body: "{}",
    });
    state.bots = state.bots.map((item) => (item.id === bot.id ? payload.bot : item));
    renderBots();
    await loadLogs();
    setMessage(`${action === "start" ? "Start" : "Stop"} complete.`, "ok");
  } catch (error) {
    setMessage(error.message, "error");
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.form.addEventListener("submit", createBot);
els.refresh.addEventListener("click", () => loadBots().catch((error) => setMessage(error.message, "error")));
els.start.addEventListener("click", () => runAction("start"));
els.stop.addEventListener("click", () => runAction("stop"));
els.reloadLogs.addEventListener("click", () => loadLogs().catch((error) => setMessage(error.message, "error")));

loadBots().catch((error) => setMessage(error.message, "error"));
