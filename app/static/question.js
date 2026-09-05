const root = document.querySelector("#question-detail");
const publicId = decodeURIComponent(
  location.pathname.split("/").filter(Boolean).pop(),
);
const i18n = window.DearFutureI18n;
const t = i18n.t;

i18n.init("page.detailTitle");

const escapeText = (value) =>
  String(value ?? "").replace(
    /[&<>\"]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char],
  );

const formatDate = (value) => i18n.formatDate(value, true);

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

const safeUrl = (value) => (/^https?:\/\//i.test(value) ? value : "#");

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

function journeyState(status) {
  const states = {
    scheduled: {
      icon: "🐌",
      title: t("journey.scheduledTitle"),
      text: t("journey.scheduledText"),
    },
    verifying: {
      icon: "🔎",
      title: t("journey.verifyingTitle"),
      text: t("journey.verifyingText"),
    },
    retry_pending: {
      icon: "🌫️",
      title: t("journey.retryTitle"),
      text: t("journey.retryText"),
    },
    failed: {
      icon: "🧭",
      title: t("journey.failedTitle"),
      text: t("journey.failedText"),
    },
  };
  return states[status] || states.scheduled;
}

function renderJourney(item) {
  const journey = journeyState(item.status);
  return `
    <section class="waiting">
      <span>${journey.icon}</span>
      <h2>${escapeText(journey.title)}</h2>
      <p>${escapeText(journey.text)}</p>
      <small>${escapeText(
        t("journey.expected", { arrival: arrivalLabel(item.check_at) }),
      )}</small>
    </section>`;
}

let question = null;

function render(item) {
  const resolved = item.status === "resolved";
  document.title = `${item.question} — DearFuture`;
  root.innerHTML = `
    <article>
      <p class="eyebrow">${escapeText(
        t("detail.about", { category: categoryLabel(item.category) }),
      )}</p>
      <h1 class="detail-title">${escapeText(item.question)}</h1>
      <div class="timeline">
        <span>${escapeText(
          t("detail.sent", { date: formatDate(item.created_at) }),
        )}</span><i></i>
        <span>${escapeText(
          t("detail.promised", { arrival: arrivalLabel(item.check_at) }),
        )}</span>
      </div>
      ${
        resolved
          ? `
            <section class="verdict">
              <p class="eyebrow">${escapeText(t("detail.note"))}</p>
              <strong>${escapeText(outcomeLabel(item.outcome))}</strong>
            </section>
            <section class="letter">
              <p>${escapeText(t("detail.salutation"))}</p>
              <div>${escapeText(item.future_letter).replace(/\n/g, "<br>")}</div>
            </section>
            <details class="sources">
              <summary>${escapeText(t("detail.sources"))}</summary>
              <div>
                ${
                  item.evidence.length
                    ? item.evidence
                        .map(
                          (source) => `
                            <a href="${escapeText(safeUrl(source.url))}" target="_blank" rel="noopener">
                              <strong>${escapeText(source.title)}</strong>
                              <span>${escapeText(source.excerpt)}</span>
                            </a>`,
                        )
                        .join("")
                    : `<p>${escapeText(t("detail.noSources"))}</p>`
                }
              </div>
            </details>`
          : renderJourney(item)
      }
      <div class="share-row">
        <button id="share-button">${escapeText(t("detail.share"))}</button>
        <span id="share-message"></span>
      </div>
    </article>`;

  document
    .querySelector("#share-button")
    .addEventListener("click", async () => {
      const shareData = {
        title: "DearFuture",
        text: item.question,
        url: location.href,
      };
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(location.href);
        document.querySelector("#share-message").textContent =
          t("detail.copied");
      }
    });
}

function renderNotFound() {
  root.innerHTML = `<p class="empty">${escapeText(
    t("detail.notFound"),
  )}<br><a href="/">${escapeText(t("detail.home"))}</a></p>`;
}

window.addEventListener("dearfuture:languagechange", () => {
  if (question) render(question);
});

fetch(`/api/questions/${encodeURIComponent(publicId)}`)
  .then((response) => {
    if (!response.ok) throw new Error();
    return response.json();
  })
  .then((item) => {
    question = item;
    render(item);
  })
  .catch(renderNotFound);
