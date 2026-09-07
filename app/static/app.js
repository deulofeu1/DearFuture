const form = document.querySelector("#question-form");
const message = document.querySelector("#form-message");
const progress = document.querySelector("#submission-progress");
const progressLabel = document.querySelector("#progress-label");
const progressStep = document.querySelector("#progress-step");
const progressBar = document.querySelector("#progress-bar");
const wall = document.querySelector("#question-wall");
const filter = document.querySelector("#category-filter");
const i18n = window.DearFutureI18n;
const t = i18n.t;

i18n.init("page.homeTitle");

const escapeText = (value) =>
  String(value ?? "").replace(
    /[&<>\"]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char],
  );

const formatDate = (value) => i18n.formatDate(value);

function periodLabel(value) {
  const hour = new Date(value).getHours();
  if (hour < 10) return t("period.morning");
  if (hour < 14) return t("period.noon");
  if (hour < 17) return t("period.afternoon");
  if (hour < 20) return t("period.dusk");
  return t("period.night");
}

const arrivalLabel = (value) =>
  t("time.arrival", { date: formatDate(value), period: periodLabel(value) });

function statusLabel(status, checkAt) {
  const labels = {
    resolved: t("status.resolved"),
    verifying: t("status.verifying"),
    retry_pending: t("status.retry"),
    failed: t("status.failed"),
  };
  return (
    labels[status] || t("status.scheduled", { arrival: arrivalLabel(checkAt) })
  );
}

function categoryLabel(category) {
  return t(`category.${category || "general"}`);
}

function outcomeLabel(outcome) {
  const keys = {
    happened: "outcome.happened",
    partially_happened: "outcome.partial",
    did_not_happen: "outcome.notHappened",
    uncertain: "outcome.uncertain",
  };
  return t(keys[outcome] || "outcome.fallback");
}

function renderWall(items) {
  if (!items.length) {
    wall.innerHTML = `<p class="empty">${escapeText(t("wall.empty"))}</p>`;
    return;
  }

  wall.innerHTML = items
    .map(
      (item) => `
        <a class="card" href="/q/${encodeURIComponent(item.public_id)}">
          <div class="card-top">
            <span>${escapeText(categoryLabel(item.category))}</span>
            <span>${escapeText(statusLabel(item.status, item.check_at))}</span>
          </div>
          <h3>${escapeText(item.question)}</h3>
          <p class="card-meta">${escapeText(
            t("wall.sent", {
              date: formatDate(item.created_at),
              arrival: arrivalLabel(item.check_at),
            }),
          )}</p>
          ${
            item.status === "resolved"
              ? `<div class="result"><strong>${escapeText(outcomeLabel(item.outcome))}</strong></div>`
              : ""
          }
          <span class="card-link">${escapeText(
            t(item.status === "resolved" ? "wall.open" : "wall.track"),
          )} →</span>
        </a>`,
    )
    .join("");
}

let wallItems = [];
let processingTimer = null;
let processingStep = 0;
let submissionStatus = "idle";

function updateProgress(state, percent, label, step = "") {
  progress.hidden = false;
  progress.dataset.state = state;
  progressLabel.textContent = label;
  progressStep.textContent = step;
  progressBar.style.width = `${percent}%`;
}

function showProcessingMessage() {
  const currentStep = processingStep + 1;
  const progressValues = [25, 60, 88];
  submissionStatus = "processing";
  message.className = "form-message processing";
  message.textContent = t(`form.processing${currentStep}`);
  updateProgress(
    "processing",
    progressValues[processingStep],
    t(`form.progress${currentStep}`),
    t("form.progressStep", { current: currentStep }),
  );
}

function startProcessingMessages() {
  stopProcessingMessages();
  processingStep = 0;
  showProcessingMessage();
  processingTimer = window.setInterval(() => {
    processingStep = Math.min(processingStep + 1, 2);
    showProcessingMessage();
  }, 3000);
}

function stopProcessingMessages() {
  if (processingTimer !== null) {
    window.clearInterval(processingTimer);
    processingTimer = null;
  }
}

async function loadWall() {
  const query = filter.value
    ? `?category=${encodeURIComponent(filter.value)}`
    : "";
  try {
    const response = await fetch(`/api/public/questions${query}`);
    if (!response.ok) throw new Error();
    wallItems = await response.json();
    renderWall(wallItems);
  } catch (_) {
    wall.innerHTML = `<p class="empty">${escapeText(t("wall.error"))}</p>`;
  }
}

async function loadStats() {
  try {
    const response = await fetch("/api/public/stats");
    if (!response.ok) return;
    const stats = await response.json();
    const values = [
      stats.total_public,
      stats.awaiting_future,
      stats.resolved,
      stats.happened,
    ];
    document.querySelectorAll("#stats strong").forEach((node, index) => {
      node.textContent = values[index];
    });
  } catch (_) {
    // The wall remains usable if the decorative summary is unavailable.
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const checkAt = new Date(
    `${data.get("check_date")}T${data.get("check_period")}:00`,
  );
  if (checkAt <= new Date()) {
    submissionStatus = "failed";
    updateProgress("failed", 0, t("form.progressFailed"));
    message.className = "form-message failed";
    message.textContent = t("form.past");
    return;
  }
  const payload = {
    question: data.get("question"),
    check_at: checkAt.toISOString(),
    is_public: true,
  };

  const button = form.querySelector("button[type='submit']");
  startProcessingMessages();
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    const response = await fetch("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : t("form.failed");
      const error = new Error(detail);
      error.isClarification = response.status === 422 && typeof body.detail === "string";
      throw error;
    }
    submissionStatus = "success";
    updateProgress("success", 100, t("form.progressSuccess"), "✓");
    message.className = "form-message success";
    message.innerHTML = body.public_request_approved
      ? `${escapeText(t("form.successPublic"))} <a href="/q/${encodeURIComponent(body.public_id)}">${escapeText(t("form.journey"))} →</a>`
      : escapeText(t("form.successPrivate"));
    form.reset();
    setDefaultCheckTime();
    await Promise.all([loadWall(), loadStats()]);
  } catch (error) {
    submissionStatus = error.isClarification ? "clarification" : "failed";
    if (error.isClarification) {
      updateProgress("clarification", 58, t("form.progressClarification"), "!");
      message.className = "form-message clarification";
      message.textContent = `${t("form.clarificationIntro")} ${error.message}`;
    } else {
      updateProgress("failed", 0, t("form.progressFailed"));
      message.className = "form-message failed";
      message.textContent = error.message;
    }
  } finally {
    stopProcessingMessages();
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
});

function setDefaultCheckTime() {
  const input = form.elements.check_date;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const localDate = new Date(
    tomorrow.getTime() - tomorrow.getTimezoneOffset() * 60_000,
  );
  input.min = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 10);
  input.value = localDate.toISOString().slice(0, 10);
  form.elements.check_period.value = "12:00";
}

window.addEventListener("dearfuture:languagechange", () => {
  if (processingTimer !== null) showProcessingMessage();
  else if (submissionStatus === "idle") message.textContent = "";
  renderWall(wallItems);
});
filter.addEventListener("change", loadWall);
setDefaultCheckTime();
Promise.all([loadWall(), loadStats()]);
