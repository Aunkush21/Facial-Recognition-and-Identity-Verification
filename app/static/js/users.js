const form = document.getElementById("create-user-form");
const errorEl = document.getElementById("user-error");
const successEl = document.getElementById("user-success");
const rowsBody = document.getElementById("user-rows");

// show / hide password toggles
const EYE = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>';
const EYE_OFF = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9.9 4.2A10.4 10.4 0 0 1 12 4c6.5 0 10 7 10 7a16 16 0 0 1-3 3.8"/><path d="M6.6 6.6A16 16 0 0 0 2 11s3.5 7 10 7a10 10 0 0 0 4.5-1"/><path d="m3 3 18 18"/></svg>';
document.querySelectorAll(".pw-toggle").forEach((btn) => {
  btn.innerHTML = EYE;
  btn.addEventListener("click", () => {
    const input = document.getElementById(btn.dataset.target);
    const reveal = input.type === "password";
    input.type = reveal ? "text" : "password";
    btn.innerHTML = reveal ? EYE_OFF : EYE;
    btn.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
  });
});

// ---- password reset modal ----
const pwModal = document.getElementById("pw-modal");
const pwModalSub = document.getElementById("pw-modal-sub");
const resetPw = document.getElementById("reset-pw");
const resetPw2 = document.getElementById("reset-pw2");
const resetError = document.getElementById("reset-error");
const rowSuccess = document.getElementById("row-success");
let resetTargetId = null;

function openResetModal(id, name) {
  resetTargetId = id;
  pwModalSub.textContent = `Set a new password for "${name}". Share it with them to sign in.`;
  resetPw.value = "";
  resetPw2.value = "";
  resetError.textContent = "";
  pwModal.hidden = false;
  resetPw.focus();
}
function closeResetModal() {
  pwModal.hidden = true;
  resetTargetId = null;
}

document.getElementById("reset-cancel").addEventListener("click", closeResetModal);
pwModal.addEventListener("click", (e) => { if (e.target === pwModal) closeResetModal(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !pwModal.hidden) closeResetModal(); });

document.getElementById("reset-save").addEventListener("click", async () => {
  resetError.textContent = "";
  const pw = resetPw.value;
  if (pw.length < 8) { resetError.textContent = "Password must be at least 8 characters."; return; }
  if (pw !== resetPw2.value) { resetError.textContent = "Passwords do not match."; return; }

  const res = await fetch(`/users/${resetTargetId}/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: pw }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    resetError.textContent = (body.detail && (body.detail[0]?.msg || body.detail)) || "Could not reset password.";
    return;
  }
  closeResetModal();
  rowSuccess.textContent = `Password updated for "${body.username}". Share it with them to sign in.`;
  setTimeout(() => { rowSuccess.textContent = ""; }, 6000);
});

async function loadUsers() {
  const res = await fetch("/users");
  if (res.status === 401) { window.location.href = "/login"; return; }
  if (res.status === 403) { window.location.href = "/recognize"; return; }
  const users = await res.json();

  rowsBody.innerHTML = "";
  for (const u of users) {
    const tr = document.createElement("tr");
    const name = u.label ? `${u.username} <span class="mono" style="color:var(--dim)">· ${u.label}</span>` : u.username;
    const statusBadge = u.is_active
      ? `<span class="badge success">active</span>`
      : `<span class="badge rejected">disabled</span>`;
    const toggle = u.is_active
      ? `<button class="secondary" data-action="status" data-id="${u.id}" data-active="false">Deactivate</button>`
      : `<button class="secondary" data-action="status" data-id="${u.id}" data-active="true">Reactivate</button>`;
    const reset = `<button class="secondary" data-action="reset" data-id="${u.id}" data-name="${u.username}">Reset password</button>`;
    tr.innerHTML = `
      <td>${name}</td>
      <td><span class="badge ${u.role === "admin" ? "pending" : ""}">${u.role}</span></td>
      <td>${statusBadge}</td>
      <td style="text-align:right; white-space:nowrap">${reset} ${toggle}</td>
    `;
    rowsBody.appendChild(tr);
  }

  rowsBody.querySelectorAll('button[data-action="status"]').forEach((btn) => {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      const res = await fetch(`/users/${btn.dataset.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: btn.dataset.active === "true" }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        rowSuccess.textContent = body.detail || "Could not update account.";
        setTimeout(() => { rowSuccess.textContent = ""; }, 6000);
        btn.disabled = false;
        return;
      }
      loadUsers();
    });
  });

  rowsBody.querySelectorAll('button[data-action="reset"]').forEach((btn) => {
    btn.addEventListener("click", () => openResetModal(btn.dataset.id, btn.dataset.name));
  });
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.textContent = "";
  successEl.textContent = "";

  const password = document.getElementById("u-password").value;
  const confirm = document.getElementById("u-password2").value;
  if (password !== confirm) {
    errorEl.textContent = "Passwords do not match.";
    return;
  }

  const payload = {
    username: document.getElementById("u-username").value,
    label: document.getElementById("u-label").value || null,
    role: document.getElementById("u-role").value,
    password,
  };

  const res = await fetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    errorEl.textContent = (body.detail && (body.detail[0]?.msg || body.detail)) || "Could not create account.";
    return;
  }

  successEl.textContent = `Created ${body.role} account "${body.username}".`;
  form.reset();
  loadUsers();
});

loadUsers();
