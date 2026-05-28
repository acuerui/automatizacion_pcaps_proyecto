let selected = null;
let currentView = "dashboard";
let jobsCache = [];
let healthCache = [];
let statusCache = {};

const RUNNING = ["downloading", "transforming", "loading_pg"];
const PENDING = ["detected", "downloaded", "transformed"];

async function getJson(url) {
  const response = await fetch(url);
  return await response.json();
}

async function post(url, body) {
  await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: body ? JSON.stringify(body) : "{}"
  });
  await refresh();
}

function setView(view) {
  currentView = view;
  document.querySelectorAll(".view").forEach(el => el.classList.toggle("active", el.id === `${view}-view`));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.view === view));
  document.getElementById("page-title").textContent = {
    dashboard: "Dashboard",
    captures: "Capturas",
    logs: "Logs",
    system: "Sistema"
  }[view];
  renderCurrentView();
}

async function refresh() {
  statusCache = await getJson("/api/status");
  jobsCache = (await getJson("/api/jobs")).data;
  healthCache = (await getJson("/api/health")).data;

  const dialog = document.getElementById("credentials-dialog");
  if (!statusCache.has_credentials && !dialog.open) dialog.showModal();

  renderCurrentView();
  await refreshLogs();
}

function renderCurrentView() {
  renderShell();
  renderDashboard();
  renderCaptures();
  renderHealth();
  renderRuntime();
}

function renderShell() {
  const workerTitle = statusCache.worker_enabled ? "Procesando pendientes" : "Modo manual";
  const subtitle = `Credenciales ${statusCache.has_credentials ? "ok" : "pendientes"} - workspace ${statusCache.workspace_dir || "-"} - postgres ${statusCache.ingest_to_postgres ? "on" : "off"}`;
  document.getElementById("worker-title").textContent = workerTitle;
  document.getElementById("worker-subtitle").textContent = subtitle;
}

function filteredJobs() {
  const term = document.getElementById("search").value.trim().toLowerCase();
  if (!term) return jobsCache;
  return jobsCache.filter(job => `${job.title || ""} ${job.filename || ""} ${job.status || ""}`.toLowerCase().includes(term));
}

function countsFor(jobs) {
  return {
    total: jobs.length,
    running: jobs.filter(j => RUNNING.includes(j.status)).length,
    loaded: jobs.filter(j => j.status === "loaded").length,
    failed: jobs.filter(j => j.status === "failed").length,
    pending: jobs.filter(j => PENDING.includes(j.status)).length
  };
}

function renderDashboard() {
  const jobs = filteredJobs();
  const counts = countsFor(jobs);
  const success = counts.total ? Math.round((counts.loaded / counts.total) * 100) : 0;

  document.getElementById("summary").innerHTML = [
    ["Total", counts.total],
    ["En ejecucion", counts.running],
    ["Cargadas", counts.loaded],
    ["Fallidas", counts.failed],
    ["Pendientes", counts.pending]
  ].map(([label, value]) => `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`).join("");

  document.getElementById("donut").style.setProperty("--progress", `${success * 3.6}deg`);
  document.getElementById("donut-label").textContent = `${success}%`;

  renderStatusChart(counts);
  renderRecentJobs(jobs.slice(0, 6));
}

function renderStatusChart(counts) {
  const max = Math.max(1, counts.total);
  const rows = [
    ["Cargadas", counts.loaded, "ok"],
    ["En ejecucion", counts.running, "warn"],
    ["Fallidas", counts.failed, "bad"],
    ["Pendientes", counts.pending, "neutral"]
  ];
  document.getElementById("status-chart").innerHTML = rows.map(([label, value, tone]) => `
    <div class="bar-row">
      <span>${label}</span>
      <div class="bar-track"><div class="bar-fill ${tone}" style="width:${Math.max(3, (value / max) * 100)}%"></div></div>
      <strong>${value}</strong>
    </div>`).join("");
}

function renderRecentJobs(jobs) {
  document.getElementById("recent-jobs").innerHTML = jobs.length ? jobs.map(job => `
    <button class="recent-item" onclick="selected='${escapeAttr(job.dataset_id)}'; setView('captures')">
      <span><strong>${esc(job.title || "")}</strong><small>${esc(job.filename || "")}</small></span>
      <span class="${statusClass(job.status)}">${esc(job.status)}</span>
    </button>`).join("") : `<p class="muted">Todavia no hay capturas registradas.</p>`;
}

function renderCaptures() {
  const jobs = filteredJobs();
  document.getElementById("job-count").textContent = `${jobs.length} registros`;
  document.getElementById("jobs").innerHTML = jobs.map(job => `
    <tr class="${selected === job.dataset_id ? "selected" : ""}" onclick="selectJob('${escapeAttr(job.dataset_id)}')">
      <td><strong>${esc(job.title || "")}</strong><br><span class="muted">${esc(job.filename || "")}</span></td>
      <td><span class="${statusClass(job.status)}">${esc(job.status)}</span></td>
      <td>${pipelineSteps(job)}</td>
      <td>${esc(shortDate(job.updated_at || ""))}</td>
      <td>${actionsFor(job)}</td>
    </tr>`).join("");
  renderDetails();
}

function renderHealth() {
  document.getElementById("health").innerHTML = healthCache.map(item => `
    <div class="health-card ${esc(item.status)}">
      <strong>${esc(item.name)}</strong>
      <span>${esc(item.detail)}</span>
    </div>`).join("");
}

function renderRuntime() {
  const items = [
    ["Worker", statusCache.worker_enabled ? "activo" : "parado"],
    ["Credenciales", statusCache.has_credentials ? "ok" : "pendientes"],
    ["Intervalo", `${statusCache.poll_interval_seconds || "-"} s`],
    ["Workspace", statusCache.workspace_dir || "-"],
    ["Postgres", statusCache.ingest_to_postgres ? "activado" : "desactivado"]
  ];
  document.getElementById("runtime").innerHTML = items.map(([label, value]) => `
    <div class="runtime-row"><span>${label}</span><strong>${esc(value)}</strong></div>`).join("");
}

function statusClass(status) {
  if (status === "loaded") return "pill loaded";
  if (status === "failed") return "pill failed";
  if (RUNNING.includes(status)) return "pill running";
  return "pill";
}

function stepState(job, step) {
  const order = ["detected", "downloaded", "transformed", "loaded"];
  const status = job.status;
  if (status === "failed") {
    const failedIndex = inferFailedStep(job);
    return order.indexOf(step) === failedIndex ? "failed" : order.indexOf(step) < failedIndex ? "done" : "";
  }
  const statusToStep = {
    detected: 0,
    downloading: 0,
    downloaded: 1,
    transforming: 1,
    transformed: 2,
    loading_pg: 2,
    loaded: 3
  };
  const current = statusToStep[status] ?? 0;
  const index = order.indexOf(step);
  if (status === "loaded" || index < current) return "done";
  if (index === current && status !== step) return "active";
  if (index === current && status === step && status !== "detected") return "done";
  return "";
}

function inferFailedStep(job) {
  const err = String(job.error || "");
  if (err.includes("ndjson2pg") || err.includes("Postgres")) return 2;
  if (err.includes("pcap2db")) return 1;
  if (job.downloaded_path) return 1;
  return 0;
}

function pipelineSteps(job) {
  const steps = ["detected", "downloaded", "transformed", "loaded"];
  return `<div class="steps">${steps.map(step => `<span class="step ${stepState(job, step)}"></span>`).join("")}</div>`;
}

function actionsFor(job) {
  if (RUNNING.includes(job.status) || job.status === "loaded") return "";
  if (job.status === "failed") {
    return `
      <button onclick="event.stopPropagation(); post('/api/retry',{dataset_id:'${escapeAttr(job.dataset_id)}'})">Retry</button>
      ${job.session_dir ? `<button onclick="event.stopPropagation(); post('/api/retry-postgres',{dataset_id:'${escapeAttr(job.dataset_id)}'})">Solo PG</button>` : ""}`;
  }
  const label = {
    detected: "Descargar",
    downloaded: "Continuar",
    transformed: "Cargar PG"
  }[job.status] || "Procesar";
  return `
    <button onclick="event.stopPropagation(); post('/api/process',{dataset_id:'${escapeAttr(job.dataset_id)}'})">${label}</button>`;
}

function selectJob(datasetId) {
  selected = datasetId;
  renderCaptures();
  refreshLogs();
}

function renderDetails() {
  const job = jobsCache.find(item => item.dataset_id === selected);
  if (!job) {
    document.getElementById("details").innerHTML = "Selecciona una captura para ver rutas, hash y errores.";
    return;
  }
  document.getElementById("details").innerHTML = `
    <div><span>Dataset</span><strong>${esc(job.dataset_id || "")}</strong></div>
    <div><span>PCAP</span><strong>${esc(job.downloaded_path || "")}</strong></div>
    <div><span>NDJSON</span><strong>${esc(job.session_dir || "")}</strong></div>
    <div><span>SHA256</span><strong>${esc(job.sha256 || "")}</strong></div>
    <div><span>Error</span><strong>${esc(job.error || "-")}</strong></div>`;
}

async function refreshLogs() {
  const query = selected ? `?dataset_id=${encodeURIComponent(selected)}` : "";
  const logs = (await getJson("/api/logs" + query)).data.reverse();
  document.getElementById("selected-log").textContent = selected ? "captura seleccionada" : "global";
  document.getElementById("logs").innerHTML = logs.map(line => `<div class="log-line">[${esc(line.ts)}] ${esc(line.level)} ${esc(line.message)}</div>`).join("");
  const panel = document.getElementById("logs");
  panel.scrollTop = panel.scrollHeight;
}

async function saveCredentials(event) {
  event.preventDefault();
  await post("/api/credentials", {
    user: document.getElementById("api-user").value,
    password: document.getElementById("api-password").value
  });
  document.getElementById("credentials-dialog").close();
  document.getElementById("api-password").value = "";
  await refresh();
}

function shortDate(value) {
  return String(value).replace("T", " ").replace("+00:00", "");
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

function escapeAttr(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

document.addEventListener("keydown", event => {
  if (event.ctrlKey && event.key.toLowerCase() === "k") {
    event.preventDefault();
    document.getElementById("search").focus();
  }
});

refresh();
setInterval(refresh, 3000);
