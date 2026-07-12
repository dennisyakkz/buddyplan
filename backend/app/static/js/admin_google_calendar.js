document.addEventListener("DOMContentLoaded", async () => {
    const computedUri = document.getElementById("computed-redirect-uri");
    const overrideInput = document.getElementById("redirect-uri-override");

    const defaultRedirectUri = `${location.origin}/google/callback`;
    computedUri.textContent = defaultRedirectUri;

    document.getElementById("btn-copy-uri").addEventListener("click", () => {
        const uri = overrideInput.value.trim() || defaultRedirectUri;
        navigator.clipboard.writeText(uri).then(() => showToast("URI gekopieerd", "success", 2000));
    });

    const secretInput = document.getElementById("client-secret");
    document.getElementById("btn-toggle-secret").addEventListener("click", () => {
        const show = secretInput.type === "password";
        secretInput.type = show ? "text" : "password";
        document.getElementById("btn-toggle-secret").innerHTML = show
            ? '<i class="fa-solid fa-eye-slash"></i> Verbergen'
            : '<i class="fa-solid fa-eye"></i> Tonen';
    });

    overrideInput.addEventListener("input", () => {
        computedUri.textContent = overrideInput.value.trim() || defaultRedirectUri;
    });

    try {
        const cfg = await api("/api/admin/google-calendar/config");
        document.getElementById("client-id").value = cfg.client_id || "";
        document.getElementById("client-secret").value = cfg.client_secret || "";
        overrideInput.value = cfg.redirect_uri_override || "";
        if (cfg.redirect_uri_override) {
            computedUri.textContent = cfg.redirect_uri_override;
        }
    } catch (err) {
        showToast("Laden mislukt: " + escapeHtml(err.message), "error");
    }

    document.getElementById("google-config-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            await api("/api/admin/google-calendar/config", {
                method: "PUT",
                body: JSON.stringify({
                    client_id: document.getElementById("client-id").value.trim(),
                    client_secret: document.getElementById("client-secret").value.trim(),
                    redirect_uri_override: overrideInput.value.trim(),
                }),
            });
            showToast("Instellingen opgeslagen", "success", 4000);
        } catch (err) {
            showToast("Opslaan mislukt: " + escapeHtml(err.message), "error");
        }
    });
});
