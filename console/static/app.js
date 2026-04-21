const state = {
  bots: [],
  selectedId: null,
};

const endpoints = {
  bots: "/api/bots",
  logs: (id) => `/api/bots/${id}/logs?limit=100`,
  runtimeLogs: (id) => `/api/bots/${id}/runtime-logs?tail=200`,
  start: (id) => `/api/bots/${id}/start`,
  stop: (id) => `/api/bots/${id}/stop`,
};

const modelPresets = [
  {
    label: "Llama 3.3 70B Instruct (free)",
    model: "meta-llama/llama-3.3-70b-instruct:free",
    baseUrl: "https://openrouter.ai/api/v1",
  },
  {
    label: "NVIDIA Nemotron 3 Nano 30B A3B (free)",
    model: "nvidia/nemotron-3-nano-30b-a3b:free",
    baseUrl: "https://openrouter.ai/api/v1",
  },
  {
    label: "NVIDIA Nemotron 3 Super (free)",
    model: "nvidia/nemotron-3-super-120b-a12b:free",
    baseUrl: "https://openrouter.ai/api/v1",
  },
  {
    label: "Qwen3 Coder 480B A35B (free)",
    model: "qwen/qwen3-coder:free",
    baseUrl: "https://openrouter.ai/api/v1",
  },
  {
    label: "OpenRouter Free Router (fallback, variable)",
    model: "openrouter/free",
    baseUrl: "https://openrouter.ai/api/v1",
  },
];

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
  model: document.querySelector("#provider-model"),
  providerBaseUrl: document.querySelector("#provider-base-url"),
  reloadLogs: document.querySelector("#reload-logs"),
  logs: document.querySelector("#logs"),
  reloadRuntimeLogs: document.querySelector("#reload-runtime-logs"),
  runtimeLogs: document.querySelector("#runtime-logs"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
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

function renderModelPresets() {
  els.model.innerHTML = "";
  modelPresets.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.model;
    option.dataset.baseUrl = preset.baseUrl;
    option.textContent = preset.label;
    els.model.append(option);
  });
  syncProviderBaseUrl();
}

function syncProviderBaseUrl() {
  const selected = els.model.selectedOptions[0];
  els.providerBaseUrl.value = selected?.dataset.baseUrl || "";
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
    els.selectedName.textContent = "Bot details";
    els.selectedStatus.textContent = "idle";
    els.details.innerHTML = "";
    els.start.disabled = true;
    els.stop.disabled = true;
    els.reloadLogs.disabled = true;
    els.reloadRuntimeLogs.disabled = true;
    els.logs.innerHTML = '<p class="empty">Choose a bot to view Activity.</p>';
    els.runtimeLogs.textContent = "Choose a bot to view runtime logs.";
    return;
  }

  els.selectedName.textContent = bot.name;
  els.selectedStatus.textContent = bot.status;
  els.start.disabled = bot.status === "running";
  els.stop.disabled = bot.status !== "running";
  els.reloadLogs.disabled = false;
  els.reloadRuntimeLogs.disabled = false;
  els.details.innerHTML = `
    <dt>ID</dt><dd>${escapeHtml(bot.id)}</dd>
    <dt>Allowed users</dt><dd>${escapeHtml(bot.allowed_user_ids || "not set")}</dd>
    <dt>Proxy URL</dt><dd>${escapeHtml(bot.proxy_url || "not set")}</dd>
    <dt>Timezone</dt><dd>${escapeHtml(bot.timezone || "not set")}</dd>
    <dt>Provider URL</dt><dd>${escapeHtml(bot.provider_base_url || "not set")}</dd>
    <dt>Model</dt><dd>${escapeHtml(bot.provider_model || "not set")}</dd>
    <dt>Telegram token</dt><dd>${bot.channel_secret_ref ? "stored server-side" : "not set"}</dd>
    <dt>Provider key</dt><dd>${bot.provider_secret_ref ? "stored server-side" : "not set"}</dd>
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
  await loadRuntimeLogs().catch((error) => {
    els.runtimeLogs.textContent = error.message;
  });
}

async function loadLogs() {
  if (!state.selectedId) {
    return;
  }
  const payload = await api(withCacheBust(endpoints.logs(state.selectedId)));
  renderLogs(payload.logs || []);
}

async function loadRuntimeLogs() {
  if (!state.selectedId) {
    return;
  }
  els.runtimeLogs.textContent = "Loading runtime logs...";
  const payload = await api(withCacheBust(endpoints.runtimeLogs(state.selectedId)));
  els.runtimeLogs.textContent = payload.logs || "No runtime logs yet.";
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
    syncProviderBaseUrl();
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

function withCacheBust(path) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}_=${Date.now()}`;
}

els.form.addEventListener("submit", createBot);
els.model.addEventListener("change", syncProviderBaseUrl);
els.refresh.addEventListener("click", () =>
  refreshSelected().catch((error) => setMessage(error.message, "error")),
);
els.start.addEventListener("click", () => runAction("start"));
els.stop.addEventListener("click", () => runAction("stop"));
els.reloadLogs.addEventListener("click", () => loadLogs().catch((error) => setMessage(error.message, "error")));
els.reloadRuntimeLogs.addEventListener("click", () =>
  loadRuntimeLogs().catch((error) => {
    els.runtimeLogs.textContent = error.message;
    setMessage(error.message, "error");
  }),
);

renderModelPresets();
loadBots().catch((error) => setMessage(error.message, "error"));

async function refreshSelected() {
  await loadBots();
  if (!state.selectedId) {
    return;
  }
  await loadLogs();
  await loadRuntimeLogs();
}
