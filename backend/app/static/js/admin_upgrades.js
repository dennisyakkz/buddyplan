let upgradeInfo = null;

document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("btn-upload").addEventListener("click", onUpload);
    await loadUpgradeInfo();
});

async function loadUpgradeInfo() {
    const statusEl = document.getElementById("upgrade-status");
    try {
        upgradeInfo = await api("/api/admin/dashboard-upgrade");
        renderUpgradeStatus();
    } catch (err) {
        statusEl.textContent = `Laden mislukt: ${err.message}`;
    }
}

function renderUpgradeStatus() {
    const statusEl = document.getElementById("upgrade-status");
    if (!upgradeInfo || !upgradeInfo.version) {
        statusEl.textContent = "Nog geen APK geüpload.";
        return;
    }
    const uploadedAt = upgradeInfo.uploaded_at
        ? formatDateTime(upgradeInfo.uploaded_at)
        : "onbekend";
    statusEl.innerHTML = `
        <div><strong>Versie:</strong> ${upgradeInfo.version}</div>
        <div style="margin-top:4px"><strong>Laatste upload:</strong> ${uploadedAt}</div>
    `;
}

function formatDateTime(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return date.toLocaleString("nl-NL", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

async function onUpload() {
    const fileInput = document.getElementById("apk-file");
    const uploadBtn = document.getElementById("btn-upload");
    const uploadStatus = document.getElementById("upload-status");
    const file = fileInput.files?.[0];

    if (!file) {
        showToast("Selecteer eerst een APK-bestand", "error");
        return;
    }

    const form = new FormData();
    form.append("file", file);

    uploadBtn.disabled = true;
    uploadStatus.textContent = "Bezig met uploaden…";

    try {
        const res = await fetch("/api/admin/dashboard-upgrade", {
            method: "POST",
            body: form,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Fout: ${res.status}`);
        }
        upgradeInfo = await res.json();
        renderUpgradeStatus();
        fileInput.value = "";
        uploadStatus.textContent = "Upload voltooid";
        showToast(`Versie ${upgradeInfo.version} geüpload`, "success");
    } catch (err) {
        uploadStatus.textContent = "";
        showToast(`Upload mislukt: ${err.message}`, "error");
    } finally {
        uploadBtn.disabled = false;
    }
}
