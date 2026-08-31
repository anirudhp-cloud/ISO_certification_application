// ==========================================================================
// Wired to the real backend (FastAPI + PostgreSQL). Login/register are real
// (bcrypt-hashed passwords, verified server-side) — see app/api/routes/auth.py.
// `standards` stays a static frontend-only list (which certifications are
// selectable); everything else (organizations, users, documents, versions,
// comments) is fetched from /api/*.
//
// Model: certification happens at the ORGANIZATION level (not per-application).
// A developer submits documentation on behalf of their organization, for a
// chosen standard. An auditor picks a standard, sees which organizations
// have submitted documentation for it, and reviews one at a time.
//
// Session: login/register return a signed JWT (see app/security.py). It's
// sent as `Authorization: Bearer <token>` on every write request and
// verified server-side (app/deps.py get_current_user) — a request can no
// longer just claim to be a different user the way the old X-User-Id header
// could. The token is opaque here; the frontend never inspects its contents,
// only stores and forwards it.
// ==========================================================================

const standards = [
  { id: "iso9001", code: "ISO 9001", name: "Quality Management Systems" },
  { id: "iso42001", code: "ISO/IEC 42001", name: "AI Management System" },
  { id: "iso27001", code: "ISO/IEC 27001", name: "Information Security Management" },
];

const SESSION_USER_KEY = "iso_platform_acting_user";
const SESSION_TOKEN_KEY = "iso_platform_access_token";

let accessToken = null;

// ==========================================================================
// API helpers
// ==========================================================================

async function apiGet(path) {
  const headers = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  const res = await fetch(path, { headers });
  if (!res.ok) await throwForResponse(res);
  return res.json();
}

async function apiSend(path, { method = "POST", json, formData } = {}) {
  const headers = {};
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;
  let body;
  if (formData) {
    body = formData;
  } else if (json) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }
  const res = await fetch(path, { method, headers, body });
  if (!res.ok) await throwForResponse(res);
  return res.status === 204 ? null : res.json();
}

async function throwForResponse(res) {
  const detail = await errorDetail(res);
  if (res.status === 401 && accessToken) {
    // Token expired/invalid mid-session — don't leave the user stuck
    // clicking around with a session that will never work again.
    logout();
    throw new Error(`Session expired — please log in again. (${detail})`);
  }
  throw new Error(detail);
}

async function errorDetail(res) {
  try {
    const err = await res.json();
    return typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
  } catch {
    return `${res.status}`;
  }
}

// ==========================================================================
// State
// ==========================================================================

let allOrganizations = [];
let currentDocuments = []; // documents currently shown in org-documentation-view

let actingUser = null;
let activeStandard = null;
let currentOrgId = null;       // organization currently being viewed in org-documentation view
let currentReadOnly = false;   // whether the currently-open org's documents are read-only (auditor viewing another org)
let activeView = null;         // which sidebar item is highlighted: 'organizations'|'documents'|'findings'|'review'|'gap-analysis'
let activeUploadTab = "upload";
let activeOrgTab = "join";     // registration panel: join existing vs create new org

// ==========================================================================
// Helpers
// ==========================================================================

function getOrg(id) { return allOrganizations.find(o => o.id === id); }
function getStandard(id) { return standards.find(s => s.id === id); }

function formatDate(d) {
  return new Date(d).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// The mappings modal renders verbatim quotes lifted straight out of uploaded
// documents, so anything containing markup would otherwise be parsed as HTML.
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function personaBadge(persona) {
  return `<span class="badge badge-${persona}">${persona}</span>`;
}

function standardBadge(standardId) {
  const s = getStandard(standardId);
  return `<span class="badge badge-standard-${s.id}">${s.code}</span>`;
}

function sourceBadge(sourceType) {
  const labels = { upload: "Manual Upload", share_path: "Share Path", zip: "Zip Import" };
  return `<span class="badge badge-source-${sourceType}">${labels[sourceType] || sourceType}</span>`;
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Guards every org-scoped fetch (documents/findings/review/gap-analysis/analyze)
// against a corrupted currentOrgId/activeStandard — e.g. a stale cached page
// left over from an older session. Without this, a bad value silently reaches
// the backend as the literal text "null" in the URL, surfacing as a cryptic
// UUID-parsing error instead of a clear message.
function requireOrgContext() {
  if (currentOrgId && UUID_RE.test(currentOrgId) && activeStandard) return true;
  console.error("Lost organization/standard context — currentOrgId:", currentOrgId, "activeStandard:", activeStandard);
  alert("Lost track of which organization you're viewing — returning to the organization list. If this keeps happening, do a hard refresh (Ctrl+Shift+R).");
  if (actingUser && actingUser.persona === "auditor") {
    showOrganizationsList();
  } else if (actingUser) {
    openOrgDocumentation(actingUser.organization_id, { showBack: false, readOnly: false });
  } else {
    showAuthScreen();
  }
  return false;
}

// ==========================================================================
// Auth screen (login / register)
// ==========================================================================

function showAuthScreen() {
  document.getElementById("main-app").classList.add("hidden");
  document.getElementById("standard-select-screen").classList.add("hidden");
  document.getElementById("auth-screen").classList.remove("hidden");
  showLoginPanel();
}

function showLoginPanel() {
  document.getElementById("login-panel").classList.remove("hidden");
  document.getElementById("register-panel").classList.add("hidden");
  document.getElementById("login-error").classList.add("hidden");
}

async function showRegisterPanel() {
  document.getElementById("login-panel").classList.add("hidden");
  document.getElementById("register-panel").classList.remove("hidden");
  document.getElementById("register-error").classList.add("hidden");

  allOrganizations = await apiGet("/api/organizations");
  const select = document.getElementById("register-org-select");
  select.innerHTML = allOrganizations.map(o => `<option value="${o.id}">${o.name}</option>`).join("");

  // No organizations exist yet (e.g. a fresh database) — "join existing" would
  // just be an empty dropdown, so default straight to "create new" instead.
  if (allOrganizations.length === 0) {
    document.querySelector('[data-org-tab="create"]').click();
  }
}

document.getElementById("show-register-btn").addEventListener("click", showRegisterPanel);
document.getElementById("show-login-btn").addEventListener("click", showLoginPanel);

document.querySelectorAll("[data-org-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    activeOrgTab = btn.dataset.orgTab;
    document.querySelectorAll("[data-org-tab]").forEach(b => b.classList.toggle("active", b === btn));
    document.querySelectorAll("[data-org-tab-panel]").forEach(p => {
      p.classList.toggle("hidden", p.dataset.orgTabPanel !== activeOrgTab);
    });
  });
});

document.getElementById("login-submit-btn").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errorEl = document.getElementById("login-error");
  errorEl.classList.add("hidden");
  if (!email || !password) { errorEl.textContent = "Email and password are required."; errorEl.classList.remove("hidden"); return; }

  try {
    const { access_token, user } = await apiSend("/api/auth/login", { json: { email, password } });
    onAuthenticated(user, access_token);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
});

document.getElementById("register-submit-btn").addEventListener("click", async () => {
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;
  const persona = document.getElementById("register-persona").value;
  const errorEl = document.getElementById("register-error");
  errorEl.classList.add("hidden");

  const payload = { name, email, password, persona };
  if (activeOrgTab === "create") {
    payload.organization_name = document.getElementById("register-org-name").value.trim();
    if (!payload.organization_name) { errorEl.textContent = "Organization name is required."; errorEl.classList.remove("hidden"); return; }
  } else {
    payload.organization_id = document.getElementById("register-org-select").value;
    if (!payload.organization_id) { errorEl.textContent = "Select an organization to join."; errorEl.classList.remove("hidden"); return; }
  }
  if (!name || !email || !password) { errorEl.textContent = "Name, email, and password are required."; errorEl.classList.remove("hidden"); return; }

  try {
    const { access_token, user } = await apiSend("/api/auth/register", { json: payload });
    allOrganizations = await apiGet("/api/organizations"); // pick up a newly-created org
    onAuthenticated(user, access_token);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
});

function onAuthenticated(user, token) {
  actingUser = user;
  accessToken = token;
  sessionStorage.setItem(SESSION_USER_KEY, JSON.stringify(user));
  sessionStorage.setItem(SESSION_TOKEN_KEY, token);
  document.getElementById("auth-screen").classList.add("hidden");
  renderStandardSelectScreen();
  document.getElementById("standard-select-screen").classList.remove("hidden");
}

function logout() {
  actingUser = null;
  accessToken = null;
  activeStandard = null;
  currentOrgId = null;
  currentReadOnly = false;
  activeView = null;
  document.getElementById("app-sidebar").innerHTML = "";
  sessionStorage.removeItem(SESSION_USER_KEY);
  sessionStorage.removeItem(SESSION_TOKEN_KEY);
  showAuthScreen();
}

document.getElementById("logout-btn").addEventListener("click", logout);

// ==========================================================================
// Certification select screen
// ==========================================================================

function renderStandardSelectScreen() {
  const list = document.getElementById("standard-list");
  list.innerHTML = standards.map(s => `
    <button class="standard-option" data-standard-id="${s.id}">
      <span class="standard-code standard-code-${s.id}">${s.code.replace("ISO", "").replace("/IEC", "").trim()}</span>
      <span class="standard-option-info">
        <span class="standard-option-name">${s.code}</span>
        <span class="standard-option-desc">${s.name}</span>
      </span>
    </button>
  `).join("");

  list.querySelectorAll(".standard-option").forEach(btn => {
    btn.addEventListener("click", () => {
      activeStandard = getStandard(btn.dataset.standardId);
      document.getElementById("standard-select-screen").classList.add("hidden");
      enterApp();
    });
  });
}

async function enterApp() {
  document.getElementById("main-app").classList.remove("hidden");

  if (allOrganizations.length === 0) {
    allOrganizations = await apiGet("/api/organizations");
  }
  const org = getOrg(actingUser.organization_id);
  document.getElementById("acting-user-name").textContent = actingUser.name;
  document.getElementById("acting-user-org").textContent = `· ${org ? org.name : ""}`;
  document.getElementById("acting-user-persona-wrap").innerHTML = personaBadge(actingUser.persona);
  document.getElementById("active-standard-wrap").innerHTML = standardBadge(activeStandard.id);

  // Developer: go straight to their own organization's documentation for this standard.
  // Auditor: see the list of organizations that have submitted documentation for this standard.
  if (actingUser.persona === "developer") {
    openOrgDocumentation(actingUser.organization_id, { showBack: false, readOnly: false });
  } else {
    showOrganizationsList();
  }
}

document.getElementById("switch-standard-btn").addEventListener("click", () => {
  document.getElementById("main-app").classList.add("hidden");
  renderStandardSelectScreen();
  document.getElementById("standard-select-screen").classList.remove("hidden");
});

// ==========================================================================
// Organizations list view (auditor only)
// ==========================================================================

async function showOrganizationsList() {
  hideAllMainViews();
  document.getElementById("organizations-list-view").classList.remove("hidden");
  activeView = "organizations";
  renderSidebar();
  await renderOrganizationsList();
}

async function renderOrganizationsList() {
  document.getElementById("org-list-standard-line").innerHTML =
    `Organizations with documentation submitted for ${standardBadge(activeStandard.id)}`;

  const tbody = document.getElementById("organizations-tbody");
  tbody.innerHTML = `<tr><td colspan="4">Loading…</td></tr>`;

  const rows = await Promise.all(allOrganizations.map(async org => {
    const docs = await apiGet(`/api/organizations/${org.id}/standards/${activeStandard.id}/documents`);
    return { org, docCount: docs.length };
  }));

  tbody.innerHTML = rows.map(({ org, docCount }) => {
    const isInternal = org.id === actingUser.organization_id;
    const scopeCell = isInternal
      ? '<span class="badge badge-internal">Internal</span>'
      : '<span class="badge badge-external">External</span>';
    return `
      <tr>
        <td>${org.name}</td>
        <td>${scopeCell}</td>
        <td>${docCount}</td>
        <td><button class="btn-link" data-open-org="${org.id}">Open →</button></td>
      </tr>
    `;
  }).join("");

  tbody.querySelectorAll("[data-open-org]").forEach(btn => {
    btn.addEventListener("click", () => openOrgDocumentation(btn.dataset.openOrg, { showBack: true, readOnly: true }));
  });
}

document.getElementById("back-to-organizations").addEventListener("click", showOrganizationsList);

// ==========================================================================
// Organization documentation view
// ==========================================================================

async function openOrgDocumentation(organizationId, { showBack, readOnly }) {
  currentOrgId = organizationId;
  currentReadOnly = readOnly;
  hideAllMainViews();
  document.getElementById("org-documentation-view").classList.remove("hidden");
  document.getElementById("back-to-organizations").classList.toggle("hidden", !showBack);
  activeView = "documents";
  renderSidebar();
  await renderOrgDocumentation(readOnly);
}

async function renderOrgDocumentation(readOnly) {
  const org = getOrg(currentOrgId);

  document.getElementById("org-doc-name").innerHTML = `${org ? org.name : ""} ${standardBadge(activeStandard.id)}`;
  document.getElementById("org-doc-meta").textContent = `Organization-level documentation for ${activeStandard.code}`;

  // Only the developer, on their own organization, can add documents.
  const canUpload = !readOnly && actingUser.persona === "developer" && currentOrgId === actingUser.organization_id;
  document.getElementById("add-document-panel").classList.toggle("hidden", !canUpload);
  if (canUpload) renderAdditionalStandardsCheckboxes();

  await renderDocumentsTable(readOnly);
}

// The other standards besides the one currently being viewed — lets one
// upload also count toward them (e.g. a combined Quality & AI Manual tagged
// for both ISO 42001 and ISO 9001) instead of uploading the same file twice.
function renderAdditionalStandardsCheckboxes() {
  const others = standards.filter(s => s.id !== activeStandard.id);
  const html = others.length === 0 ? "" : [
    `<div class="hint" style="margin:0 0 4px;">Also tag this upload for:</div>`,
    ...others.map(s => `<label class="checkbox-label"><input type="checkbox" class="additional-standard-checkbox" value="${s.id}" /> ${s.code}</label>`),
  ].join("");
  document.querySelectorAll("[data-additional-standards]").forEach(el => { el.innerHTML = html; });
}

async function renderDocumentsTable(readOnly) {
  if (!requireOrgContext()) return;
  const isAuditor = actingUser.persona === "auditor";
  const canUpload = !readOnly && actingUser.persona === "developer" && currentOrgId === actingUser.organization_id;

  // Analyze acts on the document set, so it sits with the documents.
  document.getElementById("run-analyze-btn").classList.toggle("hidden", !isAuditor);
  if (isAuditor) await renderPendingRunBanner();
  else document.getElementById("pending-run-banner").classList.add("hidden");

  currentDocuments = await apiGet(`/api/organizations/${currentOrgId}/standards/${activeStandard.id}/documents`);

  const tbody = document.getElementById("documents-tbody");
  const table = document.getElementById("documents-table");
  const empty = document.getElementById("documents-empty");

  if (currentDocuments.length === 0) {
    table.classList.add("hidden");
    empty.classList.remove("hidden");
    return;
  }
  table.classList.remove("hidden");
  empty.classList.add("hidden");

  tbody.innerHTML = currentDocuments.map(doc => `
      <tr>
        <td>${doc.document_name}</td>
        <td>${doc.document_type}</td>
        <td>v${doc.version_number}</td>
        <td>${doc.certification_standards.map(standardBadge).join(" ")}</td>
        <td>${doc.submitted_by_name}</td>
        <td>
          <div class="row-actions">
            ${canUpload ? `<button class="btn-link" data-reupload="${doc.document_group_id}">Reupload</button>` : ""}
            ${canUpload ? `<button class="btn-link btn-danger-link" data-delete="${doc.document_group_id}">Delete</button>` : ""}
            ${isAuditor ? `<button class="btn-link" data-mappings="${doc.id}">Requirements</button>` : ""}
            <button class="btn-link" data-versions="${doc.document_group_id}">Versions</button>
            <button class="btn-link" data-comments="${doc.id}">Comments</button>
          </div>
        </td>
      </tr>
  `).join("");

  tbody.querySelectorAll("[data-mappings]").forEach(btn => {
    btn.addEventListener("click", () => openMappingsModal(btn.dataset.mappings));
  });
  tbody.querySelectorAll("[data-versions]").forEach(btn => {
    btn.addEventListener("click", () => openVersionModal(btn.dataset.versions));
  });
  tbody.querySelectorAll("[data-comments]").forEach(btn => {
    btn.addEventListener("click", () => openCommentsModal(btn.dataset.comments));
  });
  tbody.querySelectorAll("[data-reupload]").forEach(btn => {
    btn.addEventListener("click", () => triggerReupload(btn.dataset.reupload));
  });
  tbody.querySelectorAll("[data-delete]").forEach(btn => {
    btn.addEventListener("click", () => deleteDocumentGroup(btn.dataset.delete));
  });
}

async function deleteDocumentGroup(groupId) {
  if (!confirm("Delete this document and all its versions? Any finding backed only by it reverts to Not Assessed, even if already reviewed. This is a soft delete — nothing is physically removed.")) return;
  try {
    await apiSend(`/api/documents/${groupId}`, { method: "DELETE" });
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
    return;
  }
  await renderDocumentsTable(false);
}

// ---------- Reupload (a new version — reuses the existing version-upload endpoint) ----------

let reuploadTargetGroupId = null;

function triggerReupload(groupId) {
  reuploadTargetGroupId = groupId;
  document.getElementById("reupload-file-input").click();
}

document.getElementById("reupload-file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  const groupId = reuploadTargetGroupId;
  reuploadTargetGroupId = null;
  if (!file || !groupId) return;

  const formData = new FormData();
  formData.append("file", file);
  try {
    await apiSend(`/api/documents/${groupId}/versions`, { formData });
  } catch (err) {
    alert(`Reupload failed: ${err.message}`);
  }
  e.target.value = "";
  await renderDocumentsTable(false);
});

// ---------- Upload tabs ----------

document.querySelectorAll(".tab-btn[data-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    activeUploadTab = btn.dataset.tab;
    document.querySelectorAll(".tab-btn[data-tab]").forEach(b => b.classList.toggle("active", b === btn));
    document.querySelectorAll("[data-tab-panel]").forEach(p => {
      p.classList.toggle("hidden", p.dataset.tabPanel !== activeUploadTab);
    });
  });
});

document.querySelectorAll(".submit-doc").forEach(btn => {
  btn.addEventListener("click", () => handleDocumentSubmit(btn.dataset.method, btn));
});

function additionalStandardsIn(panel) {
  return [...panel.querySelectorAll(".additional-standard-checkbox:checked")].map(cb => cb.value);
}

async function handleDocumentSubmit(method, btn) {
  const panel = btn.closest("[data-tab-panel]");
  const base = `/api/organizations/${currentOrgId}/standards/${activeStandard.id}/documents`;
  const additionalStandards = additionalStandardsIn(panel);

  try {
    if (method === "upload") {
      const name = panel.querySelector(".doc-name").value.trim();
      const type = panel.querySelector(".doc-type").value.trim();
      const fileInput = panel.querySelector(".doc-file");
      const file = fileInput.files[0];
      if (!name || !type || !file) { alert("Document name, type, and a file are all required."); return; }

      const formData = new FormData();
      formData.append("document_name", name);
      formData.append("document_type", type);
      additionalStandards.forEach(s => formData.append("additional_standards", s));
      formData.append("file", file);
      await apiSend(`${base}/upload`, { formData });

      panel.querySelector(".doc-name").value = "";
      panel.querySelector(".doc-type").value = "";
      fileInput.value = "";
    }

    if (method === "share_path") {
      const name = panel.querySelector(".doc-name").value.trim();
      const type = panel.querySelector(".doc-type").value.trim();
      const fileName = panel.querySelector(".doc-file-name").value.trim();
      const sharePath = panel.querySelector(".doc-share-path").value.trim();
      if (!name || !type || !fileName || !sharePath) { alert("All fields are required for a share-path reference."); return; }

      await apiSend(`${base}/share-path`, {
        json: {
          document_name: name, document_type: type, file_name: fileName, share_path: sharePath,
          additional_standards: additionalStandards,
        },
      });

      panel.querySelector(".doc-name").value = "";
      panel.querySelector(".doc-type").value = "";
      panel.querySelector(".doc-file-name").value = "";
      panel.querySelector(".doc-share-path").value = "";
    }

    if (method === "zip") {
      const fileInput = panel.querySelector(".doc-zip-file");
      const file = fileInput.files[0];
      if (!file) { alert("Choose a .zip file first."); return; }

      const formData = new FormData();
      additionalStandards.forEach(s => formData.append("additional_standards", s));
      formData.append("file", file);
      const result = await apiSend(`${base}/zip`, { formData });

      const resultBox = document.getElementById("zip-result");
      resultBox.classList.remove("hidden");

      // Anything the archive contained but did not become a document has to be
      // stated. A silently dropped file looks the same as one that was never in the
      // archive — and its requirements would later read as uncovered by the
      // organisation rather than as never having been read.
      const skipped = result.skipped || [];
      const skippedBlock = skipped.length === 0 ? "" : `
        <div class="zip-skipped">
          <strong>${skipped.length} entr${skipped.length === 1 ? "y" : "ies"} skipped — not uploaded:</strong>
          <ul>${skipped.map(s => `<li><code>${escapeHtml(s.path)}</code> — ${escapeHtml(s.reason)}</li>`).join("")}</ul>
        </div>`;

      const dupes = result.duplicate_names || [];
      const dupeBlock = dupes.length === 0 ? "" : `
        <div class="zip-skipped">
          <strong>${dupes.length} document name(s) already existed before this upload.</strong>
          <p>You now have two copies of each. Both will be read on the next Analyze, which
          doubles their share of the cost — delete the duplicates unless that was intended.</p>
          <ul>${dupes.map(n => `<li>${escapeHtml(n)}</li>`).join("")}</ul>
        </div>`;

      resultBox.innerHTML = `
        <strong>${result.created.length} document(s) created from ${escapeHtml(file.name)}:</strong>
        <ul>${result.created.map(d =>
          `<li>${escapeHtml(d.document_name)} <span class="zip-type">${escapeHtml(d.document_type)}</span></li>`
        ).join("")}</ul>
        ${skippedBlock}
        ${dupeBlock}`;
      fileInput.value = "";
    }
  } catch (err) {
    alert(`Submit failed: ${err.message}`);
    return;
  }

  document.querySelectorAll(".additional-standard-checkbox").forEach(cb => { cb.checked = false; });
  await renderDocumentsTable(false);
}

// ==========================================================================
// Findings / Review / Gap Analysis — all three read the SAME org+standard
// report (one backend endpoint), and differ only in which findings they show:
//   - Findings & Gap Analysis: only REVIEWED findings count as their real
//     status — an unreviewed one displays as if not_assessed, since it isn't
//     part of the permanent record yet.
//   - Review: the mirror image — only UNREVIEWED findings, with their real
//     pending status/scores, plus Save/Delete actions.
// "Analyze" (wherever it's triggered from) and Save/Delete are auditor-only,
// enforced server-side too — see app/api/routes/analyze.py and findings.py.
// ==========================================================================

let currentFindings = [];
let saveFindingTargetId = null;

document.getElementById("open-findings-btn").addEventListener("click", openFindingsView);
document.getElementById("back-to-documentation").addEventListener("click", () => {
  document.getElementById("findings-view").classList.add("hidden");
  document.getElementById("org-documentation-view").classList.remove("hidden");
});

// Hides every main view by class rather than by a hardcoded id list. The list version
// threw as soon as a view was removed — gap-analysis-view and review-view became
// filters on the Findings page, and getElementById returned null for both.
function hideAllMainViews() {
  document.querySelectorAll(".app-main > .view").forEach(view => view.classList.add("hidden"));
}

// ==========================================================================
// Persistent sidebar — always visible once logged in, so it's always clear
// which page you're on and there's a one-click way to any of the others,
// instead of relying purely on "Back to X" chains.
// ==========================================================================

// Assessment is the auditor's: how evidence was graded is their judgement, and the
// scores are unreviewed model output until they confirm them. Developers submit
// documents and read review comments; Findings, Gap Analysis and Review are all
// auditor-only. Enforced server-side too — see app/deps.py require_auditor_*.
const SIDEBAR_ITEMS = [
  { view: "organizations", label: "Organizations", auditorOnly: true, alwaysEnabled: true },
  { view: "documents", label: "Documents", auditorOnly: false, alwaysEnabled: false },
  { view: "findings", label: "Findings", auditorOnly: true, alwaysEnabled: false },
];

function renderSidebar() {
  const sidebar = document.getElementById("app-sidebar");
  if (!actingUser) { sidebar.innerHTML = ""; return; }

  const isAuditor = actingUser.persona === "auditor";
  const hasOrgContext = !!(currentOrgId && UUID_RE.test(currentOrgId));
  const items = SIDEBAR_ITEMS.filter(item => !item.auditorOnly || isAuditor);

  sidebar.innerHTML = `
    <div class="sidebar-group-label">${activeStandard ? activeStandard.code : ""}</div>
    ${items.map(item => {
      const enabled = item.alwaysEnabled || hasOrgContext;
      return `<button class="sidebar-item ${activeView === item.view ? "active" : ""}" data-nav="${item.view}" ${enabled ? "" : "disabled"}>${item.label}</button>`;
    }).join("")}
  `;
  sidebar.querySelectorAll("[data-nav]").forEach(btn => {
    btn.addEventListener("click", () => navigateSidebar(btn.dataset.nav));
  });
}

function navigateSidebar(view) {
  switch (view) {
    case "organizations": showOrganizationsList(); break;
    case "documents": openOrgDocumentation(currentOrgId, { showBack: currentReadOnly, readOnly: currentReadOnly }); break;
    case "findings": openFindingsView(); break;
  }
}

async function openFindingsView() {
  hideAllMainViews();
  document.getElementById("findings-view").classList.remove("hidden");
  activeView = "findings";
  renderSidebar();
  await renderFindingsView();
}

function statusBadge(status) {
  const labels = { met: "Met", partial: "Partial", gap: "Gap", not_applicable: "N/A", not_assessed: "Not Assessed" };
  return `<span class="badge badge-status-${status}">${labels[status] || status}</span>`;
}

// Which segment the findings table is showing. Clauses and controls are separate
// lists because only controls can be excluded — see the tabs in index.html.
let activeSegment = "clause";

// 'all' | 'pending' (no auditor decision yet) | 'gaps' (a nonconformity or OFI).
// These were three separate pages; they are three views of one table.
//
// Defaults to 'all' and is never changed by the app — only by the auditor clicking a
// tab. Requirements with no evidence have no finding row, so 'pending' excludes them;
// silently starting there hid the hardest gaps (8.2 and 8.3 on a real run).
let activeFilter = "all";

function matchesFilter(f) {
  if (activeFilter === "pending") return !!f.finding_id && !f.grade;
  if (activeFilter === "gaps") {
    const grade = f.grade || f.proposed_grade;
    return grade === "minor_nc" || grade === "major_nc" || grade === "ofi";
  }
  return true;
}

// The grades a certification body actually issues. A major NC blocks a certificate;
// an OFI does not — a distinction met/partial/gap could not express.
const GRADE_LABELS = {
  conforming: "Conforming",
  ofi: "OFI",
  minor_nc: "Minor NC",
  major_nc: "Major NC",
  not_applicable: "N/A",
};

function gradeBadge(f) {
  const grade = f.grade || f.proposed_grade;
  if (!grade) return `<span class="badge badge-grade-none">Not graded</span>`;
  // An unconfirmed grade is the machine's suggestion, not a decision — shown as
  // provisional so nobody mistakes it for an auditor's judgement.
  const provisional = !f.grade;
  return `<span class="badge badge-grade-${grade}${provisional ? " badge-provisional" : ""}"
    title="${provisional ? "Suggested — not yet confirmed by an auditor" : "Confirmed by an auditor"}"
    >${GRADE_LABELS[grade] || grade}${provisional ? " ?" : ""}</span>`;
}

// 'no evidence submitted' vs 'submitted and inadequate' — the two states the old
// status column collapsed into one.
function evidenceStateNote(f) {
  if (f.evidence_state === "no_evidence") return `<span class="evidence-none">No evidence submitted</span>`;
  if (f.evidence_state === "insufficient") return `<span class="evidence-partial">Evidence insufficient</span>`;
  return "";
}

// Annex B guidance checklist — shared by the Gap Analysis and Review views.
// Empty for clauses 4-10 (no Annex B) or a control not yet assessed.
// Only ever called for Annex A controls — clauses have no Annex B and the caller hides
// the whole section for them.
function renderGuidanceChecklist(checklist) {
  if (!checklist || checklist.length === 0) {
    return `<span class="hint" style="margin:0;">No Annex B guidance seeded for this control.</span>`;
  }
  return `<ul class="guidance-checklist">${checklist.map(point =>
    `<li class="${point.met ? "guidance-met" : "guidance-unmet"}">${point.met ? "✓" : "✗"} ${point.text}</li>`
  ).join("")}</ul>`;
}

// Sources = which document(s) plus exactly where in them — always shown
// explicitly, even when a precise location couldn't be pinned down, so the
// absence reads as "not identified" rather than as a missing feature.
// Evidence = a real quote (indented, italic) with its source as a caption
// underneath — a citation, not two disconnected lines of text.
function renderEvidenceQuote(f) {
  if (!f.evidence || f.evidence.length === 0) {
    return `<span class="hint" style="margin:0;">No evidence yet.</span>`;
  }
  const docNames = f.evidence.map(e => e.document_name).join(", ");
  const citation = f.source_location
    ? `${docNames}, ${f.source_location}`
    : `${docNames} — exact location not identified (may combine multiple documents, or predates source tracking; reupload to enable)`;

  if (!f.rationale) {
    return `<div class="evidence-list">${f.evidence.map(e => `<span>${e.document_name}</span>`).join("")}</div>
            <span class="hint" style="margin:4px 0 0;">No rationale yet.</span>`;
  }
  return `
    <blockquote class="evidence-quote">
      “${f.rationale}”
      <footer class="evidence-citation">— ${citation}</footer>
    </blockquote>
  `;
}

function documentNamesCell(f) {
  return f.evidence.length
    ? `<div class="evidence-list">${f.evidence.map(e => `<span>${e.document_name}</span>`).join("")}</div>`
    : `<span class="hint" style="margin:0;">—</span>`;
}

// ---------- Finding Detail modal — full rationale/source/guidance checklist,
// opened from a single-line row via "Open" (read-only everywhere) plus a
// Delete action when opened from the Review page. ----------

let findingDetailDeleteId = null;

function openFindingDetailModal(f, { allowDelete } = {}) {
  document.getElementById("finding-detail-modal-title").textContent = `${f.code} — ${f.title}`;
  document.getElementById("finding-detail-meta").innerHTML =
    `${statusBadge(f.status)} &nbsp; Coverage: ${f.coverage_score != null ? Math.round(f.coverage_score) : "—"} &nbsp; Relevance: ${f.relevance_score != null ? Math.round(f.relevance_score) : "—"}`;
  document.getElementById("finding-detail-evidence").innerHTML = renderEvidenceQuote(f);
  // Clauses 4-10 have no Annex B, so the section is removed rather than emptied.
  const isControl = f.requirement_type === "control";
  const guidanceWrap = document.getElementById("finding-detail-guidance-wrap");
  guidanceWrap.classList.toggle("hidden", !isControl);
  if (isControl) {
    const total = f.guidance_checklist.length;
    const met = f.guidance_checklist.filter(p => p.met).length;
    document.getElementById("finding-detail-guidance-heading").textContent =
      total ? `Annex B guidance — ${met} of ${total} satisfied` : "Annex B guidance";
    document.getElementById("finding-detail-guidance").innerHTML =
      renderGuidanceChecklist(f.guidance_checklist);
  }
  loadFindingEvidence(f.finding_id);

  const deleteWrap = document.getElementById("finding-detail-delete-wrap");
  findingDetailDeleteId = allowDelete && f.finding_id ? f.finding_id : null;
  deleteWrap.classList.toggle("hidden", !findingDetailDeleteId);

  showModal("finding-detail-modal");
}

// The verbatim quote from each contributing document. The finding's own rationale is
// the reduce step's merged narrative — prose about several documents rather than a
// quote from one — so it can't be located and isn't a citation. On a real 31-document
// run, 11 of 50 multi-document findings had no resolvable location while 363 of 364
// per-document mappings did: the citations existed but weren't reachable.
async function loadFindingEvidence(findingId) {
  const box = document.getElementById("finding-detail-doc-evidence");
  if (!findingId) {
    box.innerHTML = `<p class="hint" style="margin:0;">No evidence recorded — this requirement has not been assessed.</p>`;
    return;
  }
  box.innerHTML = `<p class="hint" style="margin:0;">Loading…</p>`;
  let data;
  try {
    data = await apiGet(`/api/findings/${findingId}/evidence`);
  } catch (err) {
    box.innerHTML = `<p class="hint" style="margin:0;">Could not load evidence: ${escapeHtml(err.message)}</p>`;
    return;
  }
  if (!data.items.length) {
    box.innerHTML = `<p class="hint" style="margin:0;">No document-level evidence stored for this finding.</p>`;
    return;
  }
  box.innerHTML = `
    <p class="hint" style="margin:0 0 8px;">${data.items.length} contributing document(s), strongest first.</p>
    ${data.items.map(i => `
      <div class="doc-evidence">
        <div class="doc-evidence-head">
          <span class="doc-evidence-name">${escapeHtml(i.document_name)}</span>
          <span class="doc-evidence-cov">${i.coverage_score != null ? Math.round(i.coverage_score) + "%" : "—"}</span>
        </div>
        ${i.quote ? `<blockquote class="mapping-quote">${escapeHtml(i.quote)}</blockquote>` : ""}
        ${i.source_location
          ? `<div class="mapping-citation">${escapeHtml(i.source_location)}</div>`
          : `<div class="mapping-citation mapping-citation-missing">Location not resolved</div>`}
        ${i.unmet_guidance_points.length
          ? `<div class="mapping-guidance"><div class="mapping-guidance-head">Annex B points not satisfied (${i.unmet_guidance_points.length})</div>
             <ul>${i.unmet_guidance_points.map(p => `<li>${escapeHtml(p)}</li>`).join("")}</ul></div>`
          : ""}
      </div>`).join("")}`;
}

document.getElementById("finding-detail-delete-btn").addEventListener("click", async () => {
  const id = findingDetailDeleteId;
  if (!id) return;
  hideModal("finding-detail-modal");
  await deleteFinding(id);
});

// Unreviewed findings used to be blanked out everywhere except the Review page —
// status forced to not_assessed, finding_id, evidence, scores and rationale all
// erased — on the reasoning that an unconfirmed result isn't part of the record yet.
//
// That was removed, for two reasons:
//
//   1. It made the Findings page unreadable. The M5 grade fields (proposed_grade,
//      evidence_state) were added later and never included in the blanking, so the
//      page rendered grade badges and "Evidence insufficient" over rows whose data
//      had been erased — tags with nothing behind them — and Open did nothing at all
//      because finding_id had been nulled.
//   2. It is no longer needed. A suggestion is now visibly distinct from a decision:
//      an unconfirmed grade renders dashed with a "?" and the row says Suggested.
//      Hiding the result was a blunt substitute for being able to label it.
//
// So the page shows what was actually found, and says plainly what is confirmed.
function confirmationBadge(f) {
  // No finding row means no document provided any evidence for this requirement, so
  // there is nothing to confirm or override yet. Said explicitly, because a grade
  // badge with no marker beside it would read as an assessment somebody made.
  if (!f.finding_id) return `<span class="badge badge-unassessed">Not assessed</span>`;
  return f.grade
    ? `<span class="badge badge-confirmed">Confirmed</span>`
    : `<span class="badge badge-suggested">Suggested</span>`;
}

async function renderFindingsView() {
  if (!requireOrgContext()) return;
  const org = getOrg(currentOrgId);
  document.getElementById("findings-org-name").innerHTML = `${org ? org.name : ""}`;
  document.getElementById("findings-standard-wrap").innerHTML = standardBadge(activeStandard.id);

  const isAuditor = actingUser.persona === "auditor";

  const report = await apiGet(`/api/organizations/${currentOrgId}/standards/${activeStandard.id}/report`);
  currentFindings = report.findings;
  renderFindingsSummary(report);
  renderSegmentTabs(report);
  renderFilterTabs(currentFindings.filter(f => f.requirement_type === activeSegment));
  renderFindingsTable(
    currentFindings.filter(f => f.requirement_type === activeSegment && matchesFilter(f))
  );
}

// Tab counts come from the server's per-segment summaries, so "1 of 32" is the
// standard's own total rather than a number hardcoded in the frontend (ISO 9001 has
// no controls at all).
function renderSegmentTabs(report) {
  document.getElementById("findings-col-requirement").textContent =
    activeSegment === "control" ? "Annex A control" : "Clause";
  const counts = { clause: report.clauses, control: report.controls };
  document.querySelectorAll("#findings-segment-tabs .segment-tab").forEach(tab => {
    const summary = counts[tab.dataset.segment];
    const label = tab.dataset.segment === "clause" ? "Clauses 4–10" : "Annex A controls";
    tab.textContent = summary ? `${label} (${summary.total})` : label;
    tab.classList.toggle("active", tab.dataset.segment === activeSegment);
  });
}

// Counts are of the CURRENT segment, so "Needs review (31)" means 31 clauses, not 61
// requirements — otherwise the number contradicts the table under it.
function renderFilterTabs(inSegment) {
  const counts = {
    all: inSegment.length,
    pending: inSegment.filter(f => f.finding_id && !f.grade).length,
    gaps: inSegment.filter(f => ["minor_nc", "major_nc", "ofi"].includes(f.grade || f.proposed_grade)).length,
  };
  const labels = { all: "All", pending: "Needs review", gaps: "Nonconformities" };
  document.querySelectorAll("#findings-filter-tabs .filter-tab").forEach(tab => {
    const key = tab.dataset.filter;
    tab.textContent = `${labels[key]} (${counts[key]})`;
    tab.classList.toggle("active", key === activeFilter);
  });
}

document.getElementById("findings-filter-tabs").addEventListener("click", (e) => {
  const tab = e.target.closest(".filter-tab");
  if (!tab) return;
  activeFilter = tab.dataset.filter;
  renderFindingsView();
});

document.getElementById("findings-segment-tabs").addEventListener("click", (e) => {
  const tab = e.target.closest(".segment-tab");
  if (!tab) return;
  activeSegment = tab.dataset.segment;
  renderFindingsView();
});

// Shows the most recent run whenever it hasn't been turned into findings yet. Analyze
// is a long request — 17 minutes on a real 31-document set — and until this existed the
// UI's only route to a run was that request's own response, so a browser timeout or a
// page reload made a completed run unreachable. It was still in the database; there was
// simply no way to ask for it.
async function renderPendingRunBanner() {
  const banner = document.getElementById("pending-run-banner");
  let run;
  try {
    run = await apiGet(`/api/organizations/${currentOrgId}/standards/${activeStandard.id}/runs/latest`);
  } catch {
    banner.classList.add("hidden");
    return;
  }
  if (!run || run.status === "accepted") {
    banner.classList.add("hidden");
    return;
  }

  banner.classList.remove("hidden");

  if (run.status === "running") {
    banner.className = "pending-run pending-run-info";
    banner.innerHTML = `<strong>An analysis is running.</strong>
      <p>Started ${formatDate(run.started_at)} over ${run.document_count} document(s).
      Reload this page to check again — it does not need the tab that started it.</p>`;
    return;
  }

  if (run.status === "failed") {
    banner.className = "pending-run pending-run-failed";
    banner.innerHTML = `<strong>The last analysis did not finish.</strong>
      <p>${escapeHtml(run.error_message || "No reason recorded.")}</p>
      <p>Nothing was graded. Run Analyze again when ready.</p>`;
    return;
  }

  // coverage_ready — the useful case: results exist and are waiting for the gate.
  const cost = run.cost_usd != null ? ` · $${run.cost_usd.toFixed(2)}` : "";
  const skipped = (run.skipped_documents || []).length;
  banner.className = "pending-run pending-run-ready";
  banner.innerHTML = `
    <strong>An analysis is complete and waiting for your review.</strong>
    <p>${run.documents_read} of ${run.document_count} document(s) read${cost} ·
    clauses ${run.clauses.covered}/${run.clauses.total} ·
    controls ${run.controls.covered}/${run.controls.total}${skipped ? ` · ${skipped} document(s) skipped` : ""}</p>
    <p>No findings have been written yet.</p>
    <button class="btn btn-primary" id="open-pending-run-btn">Open coverage report</button>`;
  document.getElementById("open-pending-run-btn")
    .addEventListener("click", () => openGateModal(run));
}

function renderFindingsSummary(report) {
  // Blocking is called out on its own because it's the only count that actually
  // stops a certificate — a total that lumps OFIs in with major NCs implies every
  // gap is equally serious.
  const o = report.overall;
  const blocking = o.blocking > 0
    ? `<div class="summary-stat summary-stat-blocking"><strong>${o.blocking}</strong> blocking (major NC)</div>`
    : `<div class="summary-stat summary-stat-clear"><strong>0</strong> blocking</div>`;
  document.getElementById("findings-summary").innerHTML = `
    <div class="summary-stat"><strong>${o.conforming}</strong>/${o.total} conforming</div>
    <div class="summary-stat"><strong>${o.ofi}</strong> OFI</div>
    <div class="summary-stat"><strong>${o.minor_nc}</strong> minor NC</div>
    ${blocking}
    <div class="summary-stat summary-stat-note">Documentary review only — not a conformity determination</div>
  `;
}

function renderFindingsTable(findings) {
  const table = document.getElementById("findings-table");
  const empty = document.getElementById("findings-empty");

  if (findings.length === 0) {
    table.classList.add("hidden");
    empty.classList.remove("hidden");
    return;
  }
  table.classList.remove("hidden");
  empty.classList.add("hidden");

  let lastCategory = null;
  const rows = [];
  findings.forEach(f => {
    if (f.category !== lastCategory) {
      lastCategory = f.category;
      rows.push(`<tr class="category-row"><td colspan="5">${escapeHtml(f.category || "Uncategorized")}</td></tr>`);
    }
    const stale = f.evidence_changed_since_review
      ? `<div class="evidence-stale">Evidence changed since review</div>`
      : "";
    const na = f.is_applicable === false
      ? `<div class="applicability-note">Excluded: ${escapeHtml(f.applicability_note || "no reason recorded")}</div>`
      : "";
    rows.push(`
      <tr>
        <td>${documentNamesCell(f)}${evidenceStateNote(f)}</td>
        <td>${escapeHtml(f.code)} — ${escapeHtml(f.title)}${stale}${na}</td>
        <td>${gradeBadge(f)} ${confirmationBadge(f)}</td>
        <td>${f.coverage_score != null ? Math.round(f.coverage_score) : "—"}</td>
        <td>
          <div class="row-actions">
            <button class="btn-link" data-open-finding="${escapeHtml(f.code)}">Open</button>
            ${f.finding_id && !f.grade
              ? `<button class="btn-link" data-confirm-finding="${f.finding_id}">Confirm</button>` : ""}
            ${f.finding_id
              ? `<button class="btn-link" data-override-finding="${f.finding_id}" data-clause-code="${escapeHtml(f.code)}">Override</button>` : ""}
          </div>
        </td>
      </tr>
    `);
  });

  document.getElementById("findings-tbody").innerHTML = rows.join("");
  const tbody = document.getElementById("findings-tbody");
  tbody.querySelectorAll("[data-open-finding]").forEach(btn => {
    btn.addEventListener("click", () =>
      openFindingDetailModal(currentFindings.find(f => f.code === btn.dataset.openFinding), { allowDelete: true }));
  });
  // Confirm and Override happen here rather than on a separate page — the auditor is
  // already looking at the row and its evidence.
  tbody.querySelectorAll("[data-confirm-finding]").forEach(btn => {
    btn.addEventListener("click", () => confirmFinding(btn.dataset.confirmFinding));
  });
  tbody.querySelectorAll("[data-override-finding]").forEach(btn => {
    btn.addEventListener("click", () => openSaveFindingModal(btn));
  });
}

// Analyze is two steps with the readiness gate between them. Step 1 maps the
// documents and reports coverage but writes NO findings; the auditor sees what has
// no evidence at all before anything is graded, because "nothing submitted yet" and
// "submitted and inadequate" are the two states that matter most in a Stage 1 review
// and grading them the same way hides the difference.
async function runAnalyze(btn) {
  if (!requireOrgContext()) return;
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Analyzing…";
  let run;
  try {
    run = await apiSend(`/api/organizations/${currentOrgId}/standards/${activeStandard.id}/analyze`, { method: "POST" });
  } catch (err) {
    alert(`Analysis failed: ${err.message}`);
    return;
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
  openGateModal(run);
}

function renderMissingList(segment, label) {
  if (segment.missing_codes.length === 0) {
    return `<div class="gate-segment gate-segment-complete">
      <strong>${label}</strong> — all ${segment.total} have evidence
    </div>`;
  }
  const items = segment.missing_codes
    .map(code => `<li><span class="gate-code">${escapeHtml(code)}</span> ${escapeHtml(segment.missing_titles[code] || "")}</li>`)
    .join("");
  return `<div class="gate-segment">
    <strong>${label}</strong> — ${segment.covered} of ${segment.total} have evidence
    <div class="gate-missing-head">${segment.missing_codes.length} with no evidence at all:</div>
    <ul class="gate-missing">${items}</ul>
  </div>`;
}

function openGateModal(run) {
  const body = document.getElementById("gate-modal-body");
  const footer = document.getElementById("gate-modal-footer");

  const cost = run.cost_usd != null ? ` · $${run.cost_usd.toFixed(4)}` : "";

  // A skipped document is shown FIRST and separately from missing requirements,
  // because the two mean different things: a missing requirement is a fact about the
  // organisation's evidence, a skipped document means we never looked. Reading the
  // requirement counts as if nothing were skipped would blame the organisation for a
  // failed call.
  const skipped = run.skipped_documents || [];
  const skippedBlock = skipped.length === 0 ? "" : `
    <div class="gate-skipped">
      <strong>${skipped.length} document(s) could not be read.</strong>
      <p>These were not analysed at all, so the requirement counts below are incomplete
      by an unknown amount — a requirement shown as having no evidence may simply be
      covered by one of these. Re-run Analyze to retry them.</p>
      <ul>${skipped.map(d => `<li><span class="gate-code">${escapeHtml(d.document_name)}</span> ${escapeHtml(d.error)}</li>`).join("")}</ul>
    </div>`;

  body.innerHTML = `
    <div class="gate-meta">${run.documents_read} of ${run.document_count} document(s) read${cost}</div>
    ${skippedBlock}
    ${renderMissingList(run.clauses, "Clauses")}
    ${renderMissingList(run.controls, "Controls")}
    ${run.is_complete ? "" : `
      <div class="gate-warn">
        <strong>Coverage is incomplete.</strong>
        <p>You can add the missing documents and run Analyze again, or proceed now — in which case
        a reason is required and recorded against this run, so an assessment made on incomplete
        evidence is never mistaken for a complete one.</p>
        <label>Reason for proceeding
          <input type="text" id="gate-override-reason" placeholder="e.g. Stage 1 partial submission agreed with client" />
        </label>
      </div>`}
  `;
  footer.innerHTML = `
    <button class="btn btn-ghost" data-close="gate-modal">Add more documents first</button>
    <button class="btn btn-primary" id="gate-accept-btn">${run.is_complete ? "Accept and generate findings" : "Proceed anyway"}</button>
  `;

  footer.querySelector("[data-close]").addEventListener("click", () => hideModal("gate-modal"));
  document.getElementById("gate-accept-btn").addEventListener("click", (e) => acceptRun(run, e.currentTarget));
  showModal("gate-modal");
}

async function acceptRun(run, btn) {
  const reasonInput = document.getElementById("gate-override-reason");
  const reason = reasonInput ? reasonInput.value.trim() : "";
  if (!run.is_complete && !reason) {
    alert("A reason is required to proceed on incomplete coverage.");
    return;
  }
  btn.disabled = true;
  btn.textContent = "Generating findings…";
  try {
    await apiSend(`/api/runs/${run.id}/accept`, { method: "POST", json: { override_reason: reason || null } });
  } catch (err) {
    alert(`Could not generate findings: ${err.message}`);
    btn.disabled = false;
    return;
  }
  hideModal("gate-modal");
  // Go to Findings showing EVERYTHING. Landing on the "needs review" filter hid the
  // requirements with no evidence at all — the ones proposing a major nonconformity,
  // which have no finding row to review and so are exactly what an auditor must not
  // have filtered away. The filter is the auditor's to choose, not the app's.
  activeFilter = "all";
  await openFindingsView();
}

document.getElementById("run-analyze-btn").addEventListener("click", (e) => runAnalyze(e.currentTarget));

// ==========================================================================
// Review view — unreviewed results awaiting Save/Delete. Reachable from the
// Findings page's "Review" button, or automatically right after Analyze runs
// (see runAnalyze above — the org-wide Findings-page button is the only
// Analyze trigger now; there used to be a second one on each document row,
// removed since it triggered the exact same org-wide run under a misleading
// per-document label).
// ==========================================================================


// Confirm = save exactly as the LLM produced it, no edits — the backend
// (review_finding) already treats a "save" with no status/scores this way.
// Confirm = adopt the suggested grade as the auditor's own. Sent explicitly rather
// than left implicit, so the record shows a decision was made and not merely that
// nobody objected.
async function confirmFinding(findingId) {
  const finding = currentFindings.find(f => f.finding_id === findingId);
  const grade = finding && finding.proposed_grade;
  try {
    await apiSend(`/api/findings/${findingId}`, {
      method: "PATCH",
      json: grade ? { action: "save", grade } : { action: "save" },
    });
  } catch (err) {
    alert(`Confirm failed: ${err.message}`);
    return;
  }
  await renderFindingsView();
}

function openSaveFindingModal(btn) {
  const clauseCode = btn.dataset.clauseCode;
  const finding = currentFindings.find(f => f.code === clauseCode);
  saveFindingTargetId = btn.dataset.overrideFinding;

  document.getElementById("save-finding-modal-title").textContent = `Override — ${clauseCode}`;
  // Pre-select what the auditor is overriding, so a deliberate change is visible as
  // a change rather than a fresh choice from a default.
  const current = (finding && (finding.grade || finding.proposed_grade)) || "minor_nc";
  document.getElementById("save-finding-grade").value = current;
  document.getElementById("save-finding-coverage-score").value =
    finding && finding.coverage_score != null ? Math.round(finding.coverage_score) : 0;

  const note = document.getElementById("save-finding-suggested");
  const isControl = finding && finding.requirement_type === "control";
  note.innerHTML = finding
    ? `Suggested: <strong>${GRADE_LABELS[finding.proposed_grade] || "—"}</strong>` +
      (isControl ? "" : " · Not applicable is unavailable: clauses 4–10 are mandatory and cannot be excluded.")
    : "";
  showModal("save-finding-modal");
}

document.getElementById("submit-save-finding-btn").addEventListener("click", async () => {
  if (!saveFindingTargetId) return;
  const grade = document.getElementById("save-finding-grade").value;
  const coverageScore = Number(document.getElementById("save-finding-coverage-score").value);

  // 'not_applicable' is an Annex A decision only — the server rejects it for a clause,
  // but say so here rather than letting the auditor discover it via an error.
  const finding = currentFindings.find(f => f.finding_id === saveFindingTargetId);
  if (grade === "not_applicable" && finding && finding.requirement_type !== "control") {
    alert(`${finding.code} is a mandatory clause — clauses 4–10 cannot be marked not applicable. Only Annex A controls can be excluded.`);
    return;
  }

  try {
    await apiSend(`/api/findings/${saveFindingTargetId}`, {
      method: "PATCH",
      json: { action: "save", grade, coverage_score: coverageScore },
    });
  } catch (err) {
    alert(`Override failed: ${err.message}`);
    return;
  }
  hideModal("save-finding-modal");
  await renderFindingsView();
});

async function deleteFinding(findingId) {
  if (!confirm("Delete this unreviewed result? It reverts to Not Assessed.")) return;
  try {
    await apiSend(`/api/findings/${findingId}`, { method: "PATCH", json: { action: "delete" } });
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
    return;
  }
  await renderFindingsView();
}

// ==========================================================================
// Gap Analysis view — org-wide, filtered down to gap/partial among REVIEWED
// findings (unreviewed ones aren't part of the permanent record yet — see
// Reads the same report as Findings, no separate endpoint.
// ==========================================================================


// ==========================================================================
// Version history modal
// ==========================================================================

async function openVersionModal(groupId) {
  const versions = await apiGet(`/api/documents/${groupId}/versions`);
  document.getElementById("version-modal-title").textContent = `Version History — ${versions[0].document_name}`;
  document.getElementById("version-modal-body").innerHTML = versions.map(v => {
    const updaterName = v.updated_by ? v.updated_by_name : v.submitted_by_name;
    return `
      <div class="version-item">
        <div>
          <strong>v${v.version_number}</strong> ${sourceBadge(v.source_type)}
          <div class="version-meta">${v.file_name} · by ${updaterName} on ${formatDate(v.updated_at)}</div>
        </div>
        ${v.is_current ? '<span class="badge badge-current">Current</span>' : '<span class="badge badge-superseded">Superseded</span>'}
      </div>
    `;
  }).join("");
  showModal("version-modal");
}

// ==========================================================================
// Mappings modal — one document's clause and control structure
// ==========================================================================

// Two sections rather than one list, because the segments aren't equivalent:
// clauses 4-10 are mandatory and can never be excluded, Annex A controls are
// excludable and carry Annex B implementation guidance. Rendered from
// GET /api/documents/{id}/mappings.

function renderRequirement(m) {
  const coverage = m.coverage_score === null ? "—" : `${Math.round(m.coverage_score)}%`;
  // The citation is the point of the whole feature — a verbatim quote plus a place
  // a person can actually look. Both can be absent: OCR'd documents produce no
  // positional chunks, so the quote can't be located.
  const quote = m.rationale ? `<blockquote class="mapping-quote">${escapeHtml(m.rationale)}</blockquote>` : "";
  const citation = m.source_location
    ? `<div class="mapping-citation">${escapeHtml(m.source_location)}</div>`
    : `<div class="mapping-citation mapping-citation-missing">Location not resolved — the quote could not be matched back to the document</div>`;

  let guidance = "";
  if (m.unmet_guidance_points.length > 0) {
    guidance = `
      <div class="mapping-guidance">
        <div class="mapping-guidance-head">Annex B points not satisfied (${m.unmet_guidance_points.length} of ${m.guidance_points_total})</div>
        <ul>${m.unmet_guidance_points.map(p => `<li>${escapeHtml(p)}</li>`).join("")}</ul>
      </div>`;
  } else if (m.guidance_points_total > 0) {
    guidance = `<div class="mapping-guidance-all-met">All ${m.guidance_points_total} Annex B points satisfied</div>`;
  }

  return `
    <div class="mapping-item">
      <div class="mapping-head">
        <span class="mapping-code">${escapeHtml(m.code)}</span>
        <span class="mapping-title">${escapeHtml(m.title)}</span>
        <span class="mapping-coverage">${coverage}</span>
      </div>
      ${quote}
      ${citation}
      ${guidance}
    </div>`;
}

function renderSegment(segment, heading) {
  if (segment.mappings.length === 0) {
    return `
      <section class="mapping-segment">
        <h4>${heading} <span class="mapping-count">0 of ${segment.total}</span></h4>
        <p class="mapping-segment-empty">This document provides no evidence for any of the ${segment.total} ${heading}.</p>
      </section>`;
  }
  return `
    <section class="mapping-segment">
      <h4>${heading} <span class="mapping-count">${segment.matched} of ${segment.total}</span></h4>
      ${segment.mappings.map(renderRequirement).join("")}
    </section>`;
}

function renderMappings(data) {
  // Three distinct states. 'no_match' and 'not_analysed' both show no requirements,
  // but they mean completely different things to whoever uploaded the document, so
  // they must never render the same way.
  if (data.status === "not_analysed") {
    return `
      <div class="mapping-notice">
        <strong>Not analysed yet.</strong>
        <p>An auditor needs to run Analyze before this document's clause and control coverage can be shown.</p>
      </div>`;
  }

  if (data.status === "no_match") {
    return `
      <div class="mapping-notice mapping-notice-warn">
        <strong>Analysed — no requirements matched.</strong>
        <p>This document was read in full and provided evidence for none of the ${data.clauses.total} clauses
        or ${data.controls.total} controls. That usually means the file is out of scope, was tagged to the
        wrong standard, or its text could not be extracted. Check the file and its standard tag.</p>
      </div>`;
  }

  return `
    <div class="mapping-meta">Analysed ${formatDate(data.analysed_at)} · ${escapeHtml(data.file_name)} · v${data.version_number}</div>
    ${renderSegment(data.clauses, "Clauses 4–10")}
    ${renderSegment(data.controls, "Annex A controls")}
    <p class="mapping-disclaimer">Documentary review only — coverage is assessed from the submitted text and is
    not a conformity determination.</p>`;
}

async function openMappingsModal(documentId) {
  const data = await apiGet(`/api/documents/${documentId}/mappings`);
  document.getElementById("mappings-modal-title").textContent = `Requirements Covered — ${data.document_name}`;
  document.getElementById("mappings-modal-body").innerHTML = renderMappings(data);
  showModal("mappings-modal");
}

// ==========================================================================
// Comments modal
// ==========================================================================

let currentCommentDocumentId = null;

async function openCommentsModal(documentId) {
  currentCommentDocumentId = documentId;
  const doc = currentDocuments.find(d => d.id === documentId);
  document.getElementById("comments-modal-title").textContent = `Comments — ${doc.document_name} (v${doc.version_number})`;
  await renderComments();

  const isAuditor = actingUser.persona === "auditor";
  document.getElementById("comment-composer").classList.toggle("hidden", !isAuditor);
  document.getElementById("comment-readonly-note").classList.toggle("hidden", isAuditor);

  showModal("comments-modal");
}

async function renderComments() {
  const thread = await apiGet(`/api/documents/${currentCommentDocumentId}/comments`);
  const container = document.getElementById("comments-thread");
  if (thread.length === 0) {
    container.innerHTML = `<p class="hint" style="margin:0;">No comments yet.</p>`;
    return;
  }
  container.innerHTML = thread.map(c => `
      <div class="comment-item">
        <div class="comment-author">${c.reviewed_by_name}<span class="comment-date">${formatDate(c.created_at)}</span></div>
        <div class="comment-text">${c.comment_text}</div>
      </div>
  `).join("");
}

document.getElementById("submit-comment-btn").addEventListener("click", async () => {
  const input = document.getElementById("comment-text-input");
  const text = input.value.trim();
  if (!text) return;
  try {
    await apiSend(`/api/documents/${currentCommentDocumentId}/comments`, {
      json: { comment_text: text },
    });
  } catch (err) {
    alert(`Comment failed: ${err.message}`);
    return;
  }
  input.value = "";
  await renderComments();
});

// ==========================================================================
// Modal plumbing
// ==========================================================================

function showModal(id) { document.getElementById(id).classList.remove("hidden"); }
function hideModal(id) { document.getElementById(id).classList.add("hidden"); }

document.querySelectorAll("[data-close]").forEach(btn => {
  btn.addEventListener("click", () => hideModal(btn.dataset.close));
});
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.add("hidden");
  });
});

// ==========================================================================
// Init — resume an existing session (sessionStorage) or show the login screen.
// ==========================================================================

async function init() {
  allOrganizations = await apiGet("/api/organizations");

  const savedUser = sessionStorage.getItem(SESSION_USER_KEY);
  const savedToken = sessionStorage.getItem(SESSION_TOKEN_KEY);
  if (!savedUser || !savedToken) {
    showAuthScreen();
    return;
  }

  // A cached session must be revalidated against the server, not trusted as-is —
  // otherwise a token/user left over from a deleted or test account (e.g. after
  // a database reset) would keep rendering that stale identity indefinitely.
  accessToken = savedToken;
  try {
    actingUser = await apiGet("/api/auth/me");
    sessionStorage.setItem(SESSION_USER_KEY, JSON.stringify(actingUser));
  } catch {
    logout();
    return;
  }

  renderStandardSelectScreen();
  document.getElementById("standard-select-screen").classList.remove("hidden");
}

init().catch(err => {
  document.body.innerHTML = `<p style="padding:2rem;color:#b00;">Failed to load: ${err.message} — is the backend running?</p>`;
});
