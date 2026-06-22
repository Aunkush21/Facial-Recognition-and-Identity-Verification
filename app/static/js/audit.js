const rowsBody = document.getElementById("audit-rows");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");
const PAGE_SIZE = 50;
let offset = 0;

function shortId(id) {
  return id ? `${id.slice(0, 8)}…` : "—";
}

function fmtDetail(detail) {
  if (!detail) return "";
  return Object.entries(detail)
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : v}`)
    .join("  ");
}

async function loadPage() {
  const res = await fetch(`/audit-log?limit=${PAGE_SIZE}&offset=${offset}`);
  if (res.status === 401) {
    window.location.href = "/login";
    return;
  }
  if (res.status === 403) {
    window.location.href = "/recognize";
    return;
  }
  const rows = await res.json();

  rowsBody.innerHTML = "";
  for (const row of rows) {
    const tr = document.createElement("tr");
    const id = row.identity_id || "";
    tr.innerHTML = `
      <td class="mono">${new Date(row.timestamp).toLocaleString()}</td>
      <td>${row.event_type.replace(/_/g, " ")}</td>
      <td><span class="badge ${row.result}">${row.result}</span></td>
      <td class="mono" title="${id}">${shortId(id)}</td>
      <td class="mono">${row.confidence != null ? (row.confidence * 100).toFixed(1) + "%" : "—"}</td>
      <td class="mono">${fmtDetail(row.detail)}</td>
    `;
    rowsBody.appendChild(tr);
  }

  prevBtn.disabled = offset === 0;
  nextBtn.disabled = rows.length < PAGE_SIZE;
}

prevBtn.addEventListener("click", () => {
  offset = Math.max(0, offset - PAGE_SIZE);
  loadPage();
});

nextBtn.addEventListener("click", () => {
  offset += PAGE_SIZE;
  loadPage();
});

loadPage();
