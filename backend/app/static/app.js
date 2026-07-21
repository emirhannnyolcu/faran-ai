const state = {
  conversationId: localStorage.getItem("faran_conversation") || crypto.randomUUID(),
  language: localStorage.getItem("faran_language") || "tr",
  currentWorkflowId: null,
  currentTasks: [],
  memories: [],
  activeView: "home",
  composerStateKey: "memoryReady",
  composerStateTone: "normal",
  healthReady: false,
};

const translations = {
  tr: {
    settingsTitle: "Ayarlar", languageLabel: "Dil", navHome: "Ana sayfa", navNewGoal: "Yeni hedef", navMemory: "Hafıza",
    homeTitle: "Bugün neyi gerçekleştirmek istiyorsun?", goalPlaceholder: "Bir hedef, fikir veya karar yaz...",
    workspaceLabel: "Çalışma alanın", nowTitle: "Şimdi", lastWork: "Son çalışma", activePlan: "Aktif plan",
    memoryLabel: "Hafıza", faranAnswer: "FARAN'ın yanıtı", roadmapTitle: "Uygulanabilir yol haritan",
    verified: "Doğrulandı", nextSteps: "Sonraki adımlar", longTermMemory: "Uzun vadeli hafıza",
    memoryTitle: "Hatırladıkların, düşündüklerini büyütür.", memorySearchPlaceholder: "Bir fikir, hedef veya konu ara...",
    memoryDetail: "Hafıza detayı", insightLabel: "İçgörü", connectedMemories: "Bağlantılı hafızalar",
    memoryReady: "Hafıza hazır", connectionWaiting: "Bağlantı bekleniyor", goalWorking: "Hedef üzerinde çalışılıyor",
    retryReady: "Yeniden denemeye hazır", savedToMemory: "Hafızaya kaydedildi", healthReady: "FARAN hazır",
    healthOffline: "FARAN çevrimdışı", emptyGoal: "Önce gerçekleştirmek istediğin şeyi yaz.",
    workingTitle: "FARAN çalışıyor", failedTitle: "Bu çalışma tamamlanamadı", contextPreparing: "Hedefin bağlamı hazırlanıyor.",
    progressMemory: "İlgili hafızalar inceleniyor.", progressTasks: "Uygulanabilir adımlar oluşturuluyor.", progressResult: "Sonuç düzenleniyor.",
    workflowFailed: "FARAN bu çalışmayı tamamlayamadı.", workflowTimeout: "Çalışma beklenen sürede tamamlanamadı.",
    completedToast: "Çalışma tamamlandı ve hafızaya kaydedildi.", fallbackResult: "Sonuç hafızaya kaydedildi.",
    noTasks: "Yeni görevler oluşturulmayı bekliyor.", tasksReady: "Uygulanabilir görev hazır", taskAria: "Görevi tamamlandı olarak işaretle",
    copied: "Sonuç panoya kopyalandı.", memoryLoading: "Hafıza hazırlanıyor...", noMemory: "Henüz kalıcı bir hafıza yok. İlk hedefin tamamlandığında burada görünecek.",
    memoryRecords: "Uzun vadeli kayıt", record: "kayıt", memorySearching: "Hafıza taranıyor...", noInsight: "Bu hafıza için ayrı bir içgörü bulunmuyor.",
    connectionsLoading: "Bağlantılar hazırlanıyor...", noConnections: "Henüz güçlü bir bağlantı bulunmadı.", connection: "bağlantı",
    noNotifications: "Yeni bildirimin yok.", profileActive: "FARAN çalışma alanın aktif.",
    noWorkTitle: "Henüz bir çalışma yok", noWorkSummary: "İlk hedefini yazdığında FARAN burada kaldığın yeri hatırlayacak.",
    requestFailed: "İstek tamamlanamadı",
    prompts: {
      weeklyPlan: { label: "Haftamı planla", prompt: "Bu haftaki önceliklerimi analiz et ve üç uygulanabilir göreve dönüştür. Yanıtı Türkçe ver." },
      connectIdeas: { label: "Fikirleri bağla", prompt: "Son hafızalarımdaki ortak fikirleri bul ve aralarındaki bağlantıları Türkçe özetle." },
      createGoal: { label: "Yeni hedef oluştur", prompt: "Önümüzdeki 30 gün için odaklanabileceğim ölçülebilir bir gelişim hedefi oluştur. Yanıtı Türkçe ver." },
    },
  },
  en: {
    settingsTitle: "Settings", languageLabel: "Language", navHome: "Home", navNewGoal: "New goal", navMemory: "Memory",
    homeTitle: "What do you want to accomplish today?", goalPlaceholder: "Write a goal, idea, or decision...",
    workspaceLabel: "Your workspace", nowTitle: "Now", lastWork: "Latest work", activePlan: "Active plan",
    memoryLabel: "Memory", faranAnswer: "FARAN's response", roadmapTitle: "Your actionable roadmap",
    verified: "Verified", nextSteps: "Next steps", longTermMemory: "Long-term memory",
    memoryTitle: "What you remember expands what you can think.", memorySearchPlaceholder: "Search for an idea, goal, or topic...",
    memoryDetail: "Memory detail", insightLabel: "Insight", connectedMemories: "Connected memories",
    memoryReady: "Memory ready", connectionWaiting: "Waiting for connection", goalWorking: "Working on your goal",
    retryReady: "Ready to try again", savedToMemory: "Saved to memory", healthReady: "FARAN ready",
    healthOffline: "FARAN offline", emptyGoal: "Write what you want to accomplish first.",
    workingTitle: "FARAN is working", failedTitle: "This work could not be completed", contextPreparing: "Preparing the context for your goal.",
    progressMemory: "Reviewing relevant memories.", progressTasks: "Creating actionable steps.", progressResult: "Refining the result.",
    workflowFailed: "FARAN could not complete this work.", workflowTimeout: "The work did not finish within the expected time.",
    completedToast: "Work completed and saved to memory.", fallbackResult: "The result was saved to memory.",
    noTasks: "New tasks are waiting to be created.", tasksReady: "Actionable tasks ready", taskAria: "Mark task as complete",
    copied: "Result copied to clipboard.", memoryLoading: "Preparing memory...", noMemory: "No long-term memories yet. Your first completed goal will appear here.",
    memoryRecords: "Long-term records", record: "records", memorySearching: "Searching memory...", noInsight: "There is no separate insight for this memory.",
    connectionsLoading: "Preparing connections...", noConnections: "No strong connection has been found yet.", connection: "connection",
    noNotifications: "You have no new notifications.", profileActive: "Your FARAN workspace is active.",
    noWorkTitle: "No work yet", noWorkSummary: "Once you complete your first goal, FARAN will remember where you left off.",
    requestFailed: "Request could not be completed",
    prompts: {
      weeklyPlan: { label: "Plan my week", prompt: "Analyze my priorities for this week and turn them into three actionable tasks. Respond entirely in English." },
      connectIdeas: { label: "Connect ideas", prompt: "Find recurring ideas in my recent memories and summarize the connections in English." },
      createGoal: { label: "Create a new goal", prompt: "Create a measurable development goal I can focus on for the next 30 days. Respond entirely in English." },
    },
  },
};

const views = {
  home: document.querySelector("#home-view"),
  memory: document.querySelector("#memory-view"),
};

function t(key) {
  return translations[state.language][key] || translations.tr[key] || key;
}

function applyLanguage(language) {
  state.language = language === "en" ? "en" : "tr";
  localStorage.setItem("faran_language", state.language);
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-prompt-key]").forEach((button) => {
    const prompt = translations[state.language].prompts[button.dataset.promptKey];
    button.textContent = prompt.label;
    button.dataset.prompt = prompt.prompt;
  });
  document.querySelectorAll("[data-language]").forEach((button) => {
    const active = button.dataset.language === state.language;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  updateClock();
  setComposerState(state.composerStateKey, state.composerStateTone);
  if (state.healthReady) document.querySelector("#health-label").textContent = t("healthReady");
  updateMemoryOverview();
  if (state.activeView === "memory" && !document.querySelector("#memory-search-input").value.trim()) {
    renderMemoryList(memoriesNewestFirst());
  }
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
  }
}

function headers(json = false) {
  return json ? { "Content-Type": "application/json" } : {};
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...headers(Boolean(options.body)), ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : `${t("requestFailed")} (${response.status})`;
    throw new Error(detail);
  }
  return body;
}

function selectView(name) {
  if (!views[name]) return;
  state.activeView = name;
  Object.entries(views).forEach(([viewName, element]) => element.classList.toggle("active", viewName === name));
  document.querySelectorAll("[data-view-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTarget === name);
  });
  if (name === "memory") loadMemory();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function focusNewGoal() {
  selectView("home");
  requestAnimationFrame(() => document.querySelector("#goal-input").focus());
}

function updateClock() {
  const now = new Date();
  const locale = state.language === "en" ? "en-US" : "tr-TR";
  document.querySelector("#current-time").textContent = now.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  document.querySelector("#current-date").textContent = now.toLocaleDateString(locale, { day: "numeric", month: "short" });
  document.querySelector("#day-context").textContent = now.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long" });
}

function resizeComposer() {
  const input = document.querySelector("#goal-input");
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 230)}px`;
  document.querySelector("#character-count").textContent = `${input.value.length} / 4000`;
}

function setComposerState(key, tone = "normal") {
  state.composerStateKey = key;
  state.composerStateTone = tone;
  const target = document.querySelector("#composer-state");
  target.innerHTML = `<i data-lucide="${tone === "error" ? "circle-alert" : tone === "success" ? "check" : "brain-circuit"}"></i> ${escapeHtml(t(key))}`;
  target.dataset.tone = tone;
  refreshIcons();
}

async function runGoal() {
  const input = document.querySelector("#goal-input");
  const button = document.querySelector("#run-goal");
  const goal = input.value.trim();
  if (!goal) {
    input.focus();
    showToast(t("emptyGoal"));
    return;
  }

  button.disabled = true;
  document.querySelector("#workflow-panel").hidden = false;
  document.querySelector("#result-panel").hidden = true;
  document.querySelector("#workflow-title").textContent = t("workingTitle");
  document.querySelector("#workflow-status").textContent = t("contextPreparing");
  setComposerState("goalWorking");

  try {
    const queued = await api("/agent/workflows", {
      method: "POST",
      body: JSON.stringify({ user_input: goal, conversation_id: state.conversationId }),
    });
    state.currentWorkflowId = queued.workflow_id;
    await pollWorkflow(queued.workflow_id);
  } catch (error) {
    document.querySelector("#workflow-title").textContent = t("failedTitle");
    document.querySelector("#workflow-status").textContent = error.message;
    setComposerState("retryReady", "error");
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
}

async function pollWorkflow(id) {
  const progressCopies = [
    "contextPreparing",
    "progressMemory",
    "progressTasks",
    "progressResult",
  ];

  for (let attempt = 0; attempt < 300; attempt += 1) {
    const workflow = await api(`/agent/workflows/${id}`);
    const copyIndex = Math.min(Math.floor(attempt / 18), progressCopies.length - 1);
    document.querySelector("#workflow-status").textContent = t(progressCopies[copyIndex]);

    if (workflow.status === "completed") {
      renderResult(workflow.result || {}, id);
      document.querySelector("#workflow-panel").hidden = true;
      setComposerState("savedToMemory", "success");
      showToast(t("completedToast"));
      await loadMemory({ quiet: true });
      return;
    }
    if (workflow.status === "failed") {
      throw new Error(workflow.error || t("workflowFailed"));
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
  throw new Error(t("workflowTimeout"));
}

function renderMarkdown(value) {
  const source = String(value || "");
  if (window.marked && window.DOMPurify) {
    return window.DOMPurify.sanitize(window.marked.parse(source, { breaks: true }));
  }
  return `<p>${escapeHtml(source).replace(/\n/g, "<br>")}</p>`;
}

function renderResult(result, workflowId) {
  const panel = document.querySelector("#result-panel");
  const answer = String(result.final_answer || t("fallbackResult"));
  document.querySelector("#final-answer").innerHTML = renderMarkdown(answer);
  panel.dataset.copyValue = answer;
  panel.hidden = false;

  state.currentTasks = result.tasks || [];
  const taskList = document.querySelector("#task-list");
  taskList.innerHTML = state.currentTasks.map((task, index) => {
    const description = task.description || task.title || String(task);
    return `<li class="task-item" data-task-index="${index}">
      <button class="task-check" type="button" aria-label="${escapeHtml(t("taskAria"))}"><i data-lucide="check"></i></button>
      <p>${escapeHtml(description)}</p>
    </li>`;
  }).join("");
  document.querySelector("#tasks-block").hidden = state.currentTasks.length === 0;
  document.querySelector("#current-task-count").textContent = String(state.currentTasks.length);
  document.querySelector("#active-plan-copy").textContent = state.currentTasks.length ? t("tasksReady") : t("noTasks");
  refreshIcons();

  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  verifyResult(workflowId);
}

async function verifyResult(workflowId) {
  const verification = document.querySelector("#result-verification");
  verification.hidden = true;
  try {
    const report = await api(`/evaluations/agent/${workflowId}`);
    verification.hidden = !report.passed;
  } catch (_) {
    verification.hidden = true;
  }
}

async function loadMemory({ quiet = false } = {}) {
  const list = document.querySelector("#memory-list");
  if (!quiet) list.innerHTML = emptyState("loader-circle", t("memoryLoading"));
  try {
    state.memories = await api("/memory/");
    updateMemoryOverview();
    renderMemoryList(memoriesNewestFirst());
  } catch (error) {
    if (!quiet) list.innerHTML = emptyState("circle-alert", error.message);
  }
}

function updateMemoryOverview() {
  const count = state.memories.length;
  document.querySelector("#memory-count").textContent = String(count);
  document.querySelector("#memory-count-copy").textContent = t("memoryRecords");
  document.querySelector("#memory-total").textContent = `${count} ${t("record")}`;
  document.querySelector("#active-plan-copy").textContent = state.currentTasks.length ? t("tasksReady") : t("noTasks");

  const latest = memoriesNewestFirst()[0];
  if (!latest) {
    document.querySelector("#latest-memory-title").textContent = t("noWorkTitle");
    document.querySelector("#latest-memory-summary").textContent = t("noWorkSummary");
    return;
  }
  document.querySelector("#latest-memory-title").textContent = latest.source_title;
  document.querySelector("#latest-memory-summary").textContent = latest.summary;
}

function memoriesNewestFirst() {
  return state.memories.slice().sort((left, right) => new Date(right.created_at) - new Date(left.created_at));
}

function renderMemoryList(memories, scores = new Map()) {
  const list = document.querySelector("#memory-list");
  if (!memories.length) {
    list.innerHTML = emptyState("brain-circuit", t("noMemory"));
    refreshIcons();
    return;
  }

  list.innerHTML = memories.map((memory) => {
    const score = scores.get(memory.id);
    const meta = score === undefined ? formatDate(memory.created_at) : `%${Math.round(score * 100)} eşleşme`;
    return `<button class="memory-row" type="button" data-memory-id="${memory.id}">
      <span class="memory-main">
        <h3>${escapeHtml(memory.source_title)}</h3>
        <p>${escapeHtml(memory.summary)}</p>
      </span>
      <span class="memory-meta"><span>${escapeHtml(memory.topic)}</span><time>${escapeHtml(meta)}</time></span>
      <i data-lucide="chevron-right"></i>
    </button>`;
  }).join("");
  refreshIcons();
}

async function searchMemory(event) {
  event.preventDefault();
  const input = document.querySelector("#memory-search-input");
  const query = input.value.trim();
  document.querySelector("#clear-memory-search").hidden = !query;
  if (!query) {
    renderMemoryList(memoriesNewestFirst());
    return;
  }

  document.querySelector("#memory-list").innerHTML = emptyState("loader-circle", t("memorySearching"));
  refreshIcons();
  try {
    const response = await api("/retrieval/semantic-search", {
      method: "POST",
      body: JSON.stringify({ query, limit: 10 }),
    });
    const scores = new Map(response.results.map((result) => [result.memory.id, result.score]));
    renderMemoryList(response.results.map((result) => result.memory), scores);
  } catch (error) {
    document.querySelector("#memory-list").innerHTML = emptyState("circle-alert", error.message);
    refreshIcons();
  }
}

async function openMemory(memoryId) {
  const memory = state.memories.find((item) => item.id === Number(memoryId));
  if (!memory) return;
  const drawer = document.querySelector("#memory-drawer");
  document.querySelector("#drawer-title").textContent = memory.source_title;
  document.querySelector("#drawer-topic").textContent = `${memory.topic} · ${formatDate(memory.created_at)}`;
  document.querySelector("#drawer-summary").innerHTML = renderMarkdown(memory.summary);
  document.querySelector("#drawer-insight").textContent = memory.insights || t("noInsight");
  document.querySelector("#drawer-connections").innerHTML = emptyState("loader-circle", t("connectionsLoading"));
  drawer.hidden = false;
  document.body.style.overflow = "hidden";
  refreshIcons();

  try {
    const connections = await api(`/memory/${memory.id}/connections`);
    document.querySelector("#drawer-connections").innerHTML = connections.length
      ? connections.map((item) => `<div class="connection-item"><strong>${escapeHtml(item.target_memory.source_title)}</strong><span>%${Math.round(item.connection.score * 100)} ${escapeHtml(t("connection"))} · ${escapeHtml(item.connection.reason)}</span></div>`).join("")
      : `<p>${escapeHtml(t("noConnections"))}</p>`;
  } catch (error) {
    document.querySelector("#drawer-connections").innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  }
}

function closeMemoryDrawer() {
  document.querySelector("#memory-drawer").hidden = true;
  document.body.style.overflow = "";
}

function emptyState(icon, copy) {
  return `<div class="empty-state"><div><i data-lucide="${icon}"></i><p>${escapeHtml(copy)}</p></div></div>`;
}

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString(state.language === "en" ? "en-US" : "tr-TR", { day: "numeric", month: "short", year: "numeric" });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

let toastTimer;
function showToast(copy) {
  const toast = document.querySelector("#toast");
  window.clearTimeout(toastTimer);
  toast.textContent = copy;
  toast.hidden = false;
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3200);
}

async function checkHealth() {
  try {
    await api("/health");
    state.healthReady = true;
    document.querySelector("#health-dot").classList.add("online");
    document.querySelector("#health-label").textContent = t("healthReady");
  } catch (_) {
    state.healthReady = false;
    document.querySelector("#health-label").textContent = t("healthOffline");
    setComposerState("connectionWaiting", "error");
  }
}

document.querySelectorAll("[data-view-target]").forEach((button) => button.addEventListener("click", () => selectView(button.dataset.viewTarget)));
document.querySelectorAll("[data-action='new-goal']").forEach((button) => button.addEventListener("click", focusNewGoal));
document.querySelectorAll("[data-action='close-drawer']").forEach((button) => button.addEventListener("click", closeMemoryDrawer));
document.querySelector("#sidebar-toggle").addEventListener("click", () => {
  const shell = document.querySelector("#app-shell");
  shell.classList.toggle("sidebar-expanded");
  localStorage.setItem("faran_sidebar_expanded", String(shell.classList.contains("sidebar-expanded")));
});
document.querySelector("#goal-input").addEventListener("input", resizeComposer);
document.querySelector("#goal-input").addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") runGoal();
});
document.querySelector("#run-goal").addEventListener("click", runGoal);
document.querySelectorAll("[data-prompt-key]").forEach((button) => button.addEventListener("click", () => {
  const input = document.querySelector("#goal-input");
  input.value = button.dataset.prompt;
  resizeComposer();
  input.focus();
}));
document.querySelector("#refresh-overview").addEventListener("click", () => loadMemory());
document.querySelector("#copy-result").addEventListener("click", async () => {
  const value = document.querySelector("#result-panel").dataset.copyValue || "";
  await navigator.clipboard.writeText(value);
  showToast(t("copied"));
});
document.querySelector("#task-list").addEventListener("click", (event) => {
  const button = event.target.closest(".task-check");
  if (!button) return;
  button.closest(".task-item").classList.toggle("completed");
});
document.querySelector("#memory-search-form").addEventListener("submit", searchMemory);
document.querySelector("#memory-search-input").addEventListener("input", (event) => {
  document.querySelector("#clear-memory-search").hidden = !event.target.value.trim();
});
document.querySelector("#clear-memory-search").addEventListener("click", () => {
  const input = document.querySelector("#memory-search-input");
  input.value = "";
  document.querySelector("#clear-memory-search").hidden = true;
  renderMemoryList(memoriesNewestFirst());
  input.focus();
});
document.querySelector("#memory-list").addEventListener("click", (event) => {
  const row = event.target.closest("[data-memory-id]");
  if (row) openMemory(row.dataset.memoryId);
});
document.querySelector("#notification-button").addEventListener("click", () => showToast(t("noNotifications")));
document.querySelector("#profile-button").addEventListener("click", () => {
  const menu = document.querySelector("#profile-menu");
  menu.hidden = !menu.hidden;
  document.querySelector("#profile-button").setAttribute("aria-expanded", String(!menu.hidden));
});
document.querySelectorAll("[data-language]").forEach((button) => button.addEventListener("click", () => {
  applyLanguage(button.dataset.language);
  showToast(state.language === "tr" ? "Dil Türkçe olarak ayarlandı." : "Language set to English.");
}));
document.addEventListener("click", (event) => {
  const menu = document.querySelector("#profile-menu");
  const profileButton = document.querySelector("#profile-button");
  if (!menu.hidden && !menu.contains(event.target) && !profileButton.contains(event.target)) {
    menu.hidden = true;
    profileButton.setAttribute("aria-expanded", "false");
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !document.querySelector("#memory-drawer").hidden) closeMemoryDrawer();
});

if (localStorage.getItem("faran_sidebar_expanded") === "true") {
  document.querySelector("#app-shell").classList.add("sidebar-expanded");
}
localStorage.setItem("faran_conversation", state.conversationId);
applyLanguage(state.language);
window.setInterval(updateClock, 30_000);
resizeComposer();
refreshIcons();
checkHealth();
loadMemory({ quiet: true });
