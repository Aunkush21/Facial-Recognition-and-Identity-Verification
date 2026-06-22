const datePicker = document.getElementById("date-picker");
const summaryLine = document.getElementById("summary-line");
const rowsBody = document.getElementById("attendance-rows");
const statPresent = document.getElementById("stat-present");
const statAbsent = document.getElementById("stat-absent");
const statTotal = document.getElementById("stat-total");
const exportBtn = document.getElementById("export-btn");

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

async function loadAttendance(date) {
  const res = await fetch(`/attendance?date=${date}`);
  if (res.status === 401) {
    window.location.href = "/login";
    return;
  }
  const data = await res.json();

  statPresent.textContent = data.present;
  statAbsent.textContent = data.absent;
  statTotal.textContent = data.total;
  summaryLine.innerHTML = `<b>${data.present}</b> present of <b>${data.total}</b> on ${data.date}`;

  rowsBody.innerHTML = "";
  for (const row of data.rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">${row.external_id}</td>
      <td>${row.full_name}</td>
      <td><span class="badge ${row.status}">${row.status}</span></td>
      <td class="mono">${row.time_recorded || "—"}</td>
      <td class="mono">${row.confidence != null ? (row.confidence * 100).toFixed(1) + "%" : "—"}</td>
    `;
    rowsBody.appendChild(tr);
  }
}

exportBtn.addEventListener("click", () => {
  window.location.href = `/attendance/export?date=${datePicker.value}`;
});

datePicker.value = todayIso();
datePicker.addEventListener("change", () => loadAttendance(datePicker.value));
loadAttendance(datePicker.value);
