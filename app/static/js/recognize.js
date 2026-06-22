let cameraStream = null;
let intervalHandle = null;
const sessionId = crypto.randomUUID();

const scan = document.getElementById("scan");
const statusLine = document.getElementById("status-line");
const progressFill = document.getElementById("progress-fill");
const consensusLabel = document.getElementById("consensus-label");
const rSimilarity = document.getElementById("r-similarity");
const rLiveness = document.getElementById("r-liveness");
const rSubject = document.getElementById("r-subject");
const video = document.getElementById("video");

const STATUS_LABELS = {
  no_face: "No face detected",
  spoof_rejected: "Liveness check failed — possible spoof",
  unknown: "Face not recognized",
  verifying: "Verifying…",
  present_recorded: "Attendance recorded",
  already_present: "Already marked present today",
};

const CONSENSUS_REQUIRED = 5; // mirrors settings.consensus_frames_required default

function pct(x) {
  return x != null ? (x * 100).toFixed(1) + "%" : "—";
}

function resetReadout() {
  rSimilarity.textContent = "—";
  rLiveness.textContent = "—";
  rSubject.textContent = "—";
  consensusLabel.textContent = `0 / ${CONSENSUS_REQUIRED}`;
  progressFill.style.width = "0%";
}

async function tick() {
  const blob = await captureFrameBlob(video);
  const formData = new FormData();
  formData.append("file", blob, "frame.jpg");

  let res;
  try {
    res = await fetch(`/recognize?session_id=${sessionId}`, { method: "POST", body: formData });
  } catch (err) {
    statusLine.textContent = "Network error: " + err.message;
    return;
  }

  if (!res.ok) {
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    statusLine.textContent = "Request failed (" + res.status + ")";
    return;
  }

  const data = await res.json();
  if (!data.results || data.results.length === 0) {
    statusLine.textContent = STATUS_LABELS.no_face;
    resetReadout();
    return;
  }

  const r = data.results[0];
  statusLine.textContent = STATUS_LABELS[r.status] || r.status;

  rSimilarity.textContent = pct(r.similarity);
  rLiveness.textContent = pct(r.liveness_score);
  rSubject.textContent = r.name || "—";

  const count = r.consensus_count || 0;
  consensusLabel.textContent = `${count} / ${CONSENSUS_REQUIRED}`;
  progressFill.style.width = Math.min(100, (count / CONSENSUS_REQUIRED) * 100) + "%";
}

document.getElementById("start-btn").addEventListener("click", async () => {
  if (intervalHandle) return;
  try {
    cameraStream = await startCamera(video);
  } catch (err) {
    statusLine.textContent = "Could not access camera: " + err.message;
    return;
  }
  scan.classList.add("is-live");
  statusLine.textContent = "Scanning…";
  intervalHandle = setInterval(tick, 1000);
});

document.getElementById("stop-btn").addEventListener("click", () => {
  clearInterval(intervalHandle);
  intervalHandle = null;
  stopCamera(cameraStream);
  scan.classList.remove("is-live");
  statusLine.textContent = "Stopped.";
  resetReadout();
});
