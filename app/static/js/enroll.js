let cameraStream = null;
let mode = "camera";
let selectedFile = null;

const videoEl = document.getElementById("video");
const modeCamera = document.getElementById("mode-camera");
const modeUpload = document.getElementById("mode-upload");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const dropzoneText = document.getElementById("dropzone-text");
const uploadPreview = document.getElementById("upload-preview");

async function ensureCamera() {
  if (cameraStream) return;
  try {
    cameraStream = await startCamera(videoEl);
  } catch (err) {
    document.getElementById("enroll-error").textContent = "Could not access camera: " + err.message;
  }
}

// --- mode switching ---
document.querySelectorAll(".seg-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    mode = btn.dataset.mode;
    if (mode === "camera") {
      modeCamera.hidden = false;
      modeUpload.hidden = true;
      ensureCamera();
    } else {
      modeCamera.hidden = true;
      modeUpload.hidden = false;
      stopCamera(cameraStream);
      cameraStream = null;
    }
  });
});

// --- file upload handling ---
function setFile(file) {
  selectedFile = file;
  if (file) {
    dropzoneText.textContent = file.name;
    uploadPreview.src = URL.createObjectURL(file);
    uploadPreview.hidden = false;
  }
}
fileInput.addEventListener("change", () => setFile(fileInput.files[0] || null));
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag");
  if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});

// --- create identity (admin only) ---
const createForm = document.getElementById("create-identity-form");
if (createForm) {
  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("create-error");
    const successEl = document.getElementById("create-success");
    errorEl.textContent = "";
    successEl.textContent = "";

    const external_id = document.getElementById("external_id").value;
    const full_name = document.getElementById("full_name").value;

    const res = await fetch("/identities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ external_id, full_name }),
    });

    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      errorEl.textContent = body.detail || "Could not create identity.";
      return;
    }
    successEl.textContent = `Created identity ${body.id}`;
    document.getElementById("identity_id").value = body.id;
  });
}

// --- capture & enroll ---
document.getElementById("capture-btn").addEventListener("click", async () => {
  const errorEl = document.getElementById("enroll-error");
  const successEl = document.getElementById("enroll-success");
  errorEl.textContent = "";
  successEl.textContent = "";

  const identityId = document.getElementById("identity_id").value.trim();
  if (!identityId) {
    errorEl.textContent = "Enter an identity ID first.";
    return;
  }

  let blob;
  let filename = "capture.jpg";
  if (mode === "camera") {
    blob = await captureFrameBlob(videoEl);
  } else {
    if (!selectedFile) {
      errorEl.textContent = "Choose a photo to upload first.";
      return;
    }
    blob = selectedFile;
    filename = selectedFile.name;
  }

  const formData = new FormData();
  formData.append("file", blob, filename);

  const res = await fetch(`/identities/${identityId}/enroll`, { method: "POST", body: formData });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    errorEl.textContent = body.detail || "Enrollment failed.";
    return;
  }
  successEl.textContent = "Face enrolled successfully.";
});

ensureCamera();
