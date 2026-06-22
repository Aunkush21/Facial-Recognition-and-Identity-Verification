const sessionId = crypto.randomUUID();
const scan = document.getElementById("scan");
const statusEl = document.getElementById("kiosk-status");
const subEl = document.getElementById("kiosk-sub");
const overlay = document.getElementById("kiosk-overlay");
const card = document.getElementById("kiosk-card");
const iconEl = document.getElementById("kiosk-icon");
const nameEl = document.getElementById("kiosk-name");
const resultEl = document.getElementById("kiosk-result");
const timeEl = document.getElementById("kiosk-time");
const video = document.getElementById("video");

let paused = false; // pause polling while showing a welcome card

const CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
const INFO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';

function showCard(kind, name, result) {
  paused = true;
  card.className = "kiosk-card " + kind; // kind: ok | info
  iconEl.innerHTML = kind === "ok" ? CHECK : INFO;
  nameEl.textContent = name;
  resultEl.textContent = result;
  timeEl.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  overlay.hidden = false;
  setTimeout(() => {
    overlay.hidden = true;
    paused = false;
    statusEl.textContent = "Ready";
    subEl.textContent = "Look at the camera to check in.";
  }, 3800);
}

async function tick() {
  if (paused) return;
  let blob;
  try {
    blob = await captureFrameBlob(video);
  } catch { return; }
  const fd = new FormData();
  fd.append("file", blob, "frame.jpg");

  let res;
  try {
    res = await fetch(`/recognize?session_id=${sessionId}`, { method: "POST", body: fd });
  } catch { return; }

  if (res.status === 401) { window.location.href = "/login"; return; }
  if (!res.ok) return;

  const data = await res.json();
  if (!data.results || !data.results.length) {
    statusEl.textContent = "Ready";
    subEl.textContent = "Look at the camera to check in.";
    return;
  }

  const r = data.results[0];
  switch (r.status) {
    case "present_recorded":
      showCard("ok", r.name || "Welcome", "Marked present");
      break;
    case "already_present":
      showCard("info", r.name || "Welcome back", "Already checked in today");
      break;
    case "verifying":
      statusEl.textContent = "Verifying…";
      subEl.textContent = (r.name ? r.name + " — " : "") + "hold still";
      break;
    case "spoof_rejected":
      statusEl.textContent = "Liveness check failed";
      subEl.textContent = "Please look directly at the camera.";
      break;
    case "unknown":
      statusEl.textContent = "Not recognized";
      subEl.textContent = "Ask an operator to enroll you.";
      break;
    default:
      statusEl.textContent = "Scanning…";
      subEl.textContent = "Look at the camera to check in.";
  }
}

(async () => {
  try {
    await startCamera(video);
    scan.classList.add("is-live");
    statusEl.textContent = "Ready";
    subEl.textContent = "Look at the camera to check in.";
    setInterval(tick, 1000);
  } catch (err) {
    statusEl.textContent = "Camera unavailable";
    subEl.textContent = err.message;
  }
})();

(function () {
  const el = document.getElementById("kiosk-clock");
  const t = () => { el.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); };
  t();
  setInterval(t, 1000);
})();
