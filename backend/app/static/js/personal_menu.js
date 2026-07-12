document.addEventListener("DOMContentLoaded", async () => {
    const trigger = document.getElementById("personal-trigger");
    const dropdown = document.getElementById("personal-dropdown");
    const adminLink = document.getElementById("admin-link");
    const afvalwijzerLink = document.getElementById("afvalwijzer-link");
    const googleCalendarLink = document.getElementById("google-calendar-link");
    const upgradesLink = document.getElementById("upgrades-link");

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
            trigger.innerHTML = `${me.name} <i class="fa-solid fa-caret-down"></i>`;
        }
        if (me?.is_admin) {
            adminLink.classList.remove("hidden");
            afvalwijzerLink?.classList.remove("hidden");
            googleCalendarLink?.classList.remove("hidden");
            upgradesLink?.classList.remove("hidden");
        }
    } catch (_err) {
        // ignore
    }
});

