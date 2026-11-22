// Shared helpers for the AI monitoring pages (REQ-BE-094, REQ-BE-095, REQ-BE-097)
const aiEuro = new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR", minimumFractionDigits: 2, maximumFractionDigits: 4 });
const aiNumber = new Intl.NumberFormat("nl-NL");

function aiFormatEuro(value) {
    return value === null || value === undefined ? "onbekend" : aiEuro.format(value);
}

function aiFormatNumber(value) {
    return aiNumber.format(value || 0);
}

function aiFormatTime(iso) {
    return new Date(iso).toLocaleString("nl-NL", { dateStyle: "short", timeStyle: "medium" });
}

function aiFormatDuration(ms) {
    if (ms === null || ms === undefined) return "";
    return ms >= 1000 ? `${(ms / 1000).toFixed(1).replace(".", ",")} s` : `${ms} ms`;
}

function aiStatusBadge(status) {
    const labels = { ok: "ok", empty: "leeg", error: "fout" };
    return `<span class="ai-badge ai-badge-${escapeHtml(status)}">${escapeHtml(labels[status] || status)}</span>`;
}

function aiIsoDate(d) {
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function aiShowWideModal(html) {
    const content = document.getElementById("modal-content");
    content.classList.add("ai-modal-wide");
    showModal(html);
    const overlay = document.getElementById("modal-overlay");
    const restore = () => content.classList.remove("ai-modal-wide");
    const observer = new MutationObserver(() => {
        if (overlay.classList.contains("hidden")) {
            restore();
            observer.disconnect();
        }
    });
    observer.observe(overlay, { attributes: true, attributeFilter: ["class"] });
}
