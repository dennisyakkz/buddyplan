let toastTimer = null;

function showToast(message, type = "success", timeoutMs = 5000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    if (toastTimer) {
        clearTimeout(toastTimer);
        toastTimer = null;
    }

    container.innerHTML = `
        <div class="toast toast-${type}" role="status">
            <div class="toast-message">${message}</div>
            <button class="toast-close" type="button" aria-label="Sluiten">&times;</button>
        </div>
    `;

    const closeBtn = container.querySelector(".toast-close");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            container.innerHTML = "";
        });
    }

    toastTimer = setTimeout(() => {
        container.innerHTML = "";
        toastTimer = null;
    }, timeoutMs);
}

