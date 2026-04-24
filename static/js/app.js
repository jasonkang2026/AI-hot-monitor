/* AI Hot Monitor – frontend logic */

const SOURCE_ICONS = {
  "Hacker News": "bi-newspaper",
  GitHub: "bi-github",
};

function sourceIcon(source) {
  if (source.startsWith("r/")) return "bi-reddit";
  return SOURCE_ICONS[source] || "bi-globe";
}

let allTopics = [];
let activeSource = "all";

async function loadSources() {
  try {
    const resp = await fetch("/api/sources");
    const data = await resp.json();
    const tabs = document.getElementById("sourceTabs");
    data.sources.forEach(({ key, name }) => {
      const li = document.createElement("li");
      li.className = "nav-item";
      li.innerHTML = `<button class="nav-link" data-source="${key}">${name}</button>`;
      tabs.appendChild(li);
    });
    tabs.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-source]");
      if (!btn) return;
      tabs.querySelectorAll(".nav-link").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeSource = btn.dataset.source;
      renderTopics();
    });
  } catch (err) {
    console.error("Failed to load sources", err);
  }
}

async function loadTopics() {
  document.getElementById("loading").classList.remove("d-none");
  document.getElementById("topics-grid").classList.add("d-none");
  document.getElementById("error-state").classList.add("d-none");

  try {
    const resp = await fetch("/api/topics");
    if (!resp.ok) throw new Error("Network response was not ok");
    const data = await resp.json();
    allTopics = data.items || [];
    const updatedEl = document.getElementById("updated-at");
    if (data.updated_at) updatedEl.textContent = `Last updated: ${data.updated_at}`;
    document.getElementById("loading").classList.add("d-none");
    document.getElementById("topics-grid").classList.remove("d-none");
    renderTopics();
  } catch (err) {
    console.error("Failed to load topics", err);
    document.getElementById("loading").classList.add("d-none");
    document.getElementById("error-state").classList.remove("d-none");
  }
}

function renderTopics() {
  const container = document.getElementById("cards-container");
  container.innerHTML = "";

  const filtered =
    activeSource === "all"
      ? allTopics
      : allTopics.filter((item) => {
          if (activeSource === "hacker_news") return item.source === "Hacker News";
          if (activeSource === "github") return item.source === "GitHub";
          if (activeSource === "reddit") return item.source.startsWith("r/");
          return true;
        });

  document.getElementById("result-count").textContent = `${filtered.length} topics`;

  if (filtered.length === 0) {
    container.innerHTML =
      '<p class="text-muted text-center py-4">No topics available for this source.</p>';
    return;
  }

  filtered.forEach((item) => {
    const col = document.createElement("div");
    col.className = "col-12 col-sm-6 col-lg-4 col-xl-3";
    col.innerHTML = buildCard(item);
    container.appendChild(col);
  });
}

function buildCard(item) {
  const icon = sourceIcon(item.source);
  const scoreLabel = item.source === "GitHub" ? "stars" : "points";
  const commentsLabel = item.source === "GitHub" ? "forks" : "comments";
  const commentIcon = item.source === "GitHub" ? "bi-diagram-2" : "bi-chat";

  return `
    <div class="topic-card card">
      <div class="card-body">
        <div class="card-title">
          <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(item.title)}
          </a>
        </div>
        <div class="meta">
          <span class="badge-source">
            <i class="bi ${icon} me-1"></i>${escapeHtml(item.source)}
          </span>
          <span class="stat">
            <i class="bi bi-star-fill text-warning"></i>
            ${item.score.toLocaleString()} ${scoreLabel}
          </span>
          <span class="stat">
            <i class="bi ${commentIcon}"></i>
            ${item.comments.toLocaleString()} ${commentsLabel}
          </span>
          ${item.published_at ? `<span class="stat"><i class="bi bi-clock" aria-hidden="true"></i><span class="visually-hidden">Published: </span>${escapeHtml(item.published_at)}</span>` : ""}
        </div>
      </div>
    </div>`;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Kick off
loadSources();
loadTopics();
