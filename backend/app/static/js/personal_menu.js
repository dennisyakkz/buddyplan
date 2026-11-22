document.addEventListener("DOMContentLoaded", async () => {
    const trigger = document.getElementById("personal-trigger");
    const dropdown = document.getElementById("personal-dropdown");
    const adminLink = document.getElementById("admin-link");

    function close() {
        dropdown.classList.add("hidden");
    }

    trigger?.addEventListener("click", (e) => {
        e.preventDefault();
        dropdown.classList.toggle("hidden");
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest("#personal-menu")) close();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") close();
    });

    try {
        const me = await api("/api/me");
        if (me?.name) {
            trigger.innerHTML = `${me.name} <span class="material-symbols-rounded bp-icon-inline">expand_more</span>`;
        }
        if (me?.is_admin) {
            adminLink.classList.remove("hidden");
        }
    } catch (_err) {
        // ignore
    }
});

