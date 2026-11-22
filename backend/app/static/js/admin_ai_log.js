// AI call log (REQ-BE-094)
document.addEventListener("DOMContentLoaded", async () => {
    const rows = document.getElementById("ai-log-rows");
    const count = document.getElementById("ai-log-count");
    const prev = document.getElementById("ai-log-prev");
    const next = document.getElementById("ai-log-next");
    const person = document.getElementById("f-person");
    const status = document.getElementById("f-status");
    const activity = document.getElementById("f-activity");
    const from = document.getElementById("f-from");
    const to = document.getElementById("f-to");
    const messageNote = document.getElementById("ai-log-message-filter");
    let page = 1;
    let messageId = new URLSearchParams(location.search).get("message_id");
    let activitiesLoaded = false;

    try {
        const persons = await api("/api/persons");
        person.insertAdjacentHTML("beforeend", persons
            .map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join(""));
    } catch (_err) {
        // the filter still works without names
    }

    function showMessageNote() {
        if (!messageId) {
            messageNote.classList.add("hidden");
            return;
        }
        messageNote.classList.remove("hidden");
        messageNote.innerHTML = `Alleen de aanroepen van één chatbericht. <a href="#" id="ai-log-all">Alles tonen</a>`;
        document.getElementById("ai-log-all").addEventListener("click", (e) => {
            e.preventDefault();
            messageId = null;
            history.replaceState(null, "", location.pathname);
            page = 1;
            load();
        });
    }

    async function load() {
        const params = new URLSearchParams({ page });
        if (person.value) params.set("person_id", person.value);
        if (status.value) params.set("status", status.value);
        if (activity.value) params.set("activity", activity.value);
        if (from.value) params.set("date_from", from.value);
        if (to.value) params.set("date_to", to.value);
        if (messageId) params.set("message_id", messageId);
        showMessageNote();
        try {
            const data = await api(`/api/admin/ai/calls?${params}`);
            if (!activitiesLoaded) {
                activity.insertAdjacentHTML("beforeend", data.activities
                    .map(a => `<option value="${escapeHtml(a)}">${escapeHtml(a)}</option>`).join(""));
                activitiesLoaded = true;
            }
            render(data);
        } catch (err) {
            showToast("Laden mislukt: " + escapeHtml(err.message), "error");
        }
    }

    function render(data) {
        if (!data.items.length) {
            rows.innerHTML = '<tr><td colspan="10" class="ai-muted">Geen aanroepen gevonden.</td></tr>';
        } else {
            rows.innerHTML = data.items.map(c => `
                <tr class="ai-clickable" data-id="${c.id}">
                    <td>${escapeHtml(aiFormatTime(c.created_at))}</td>
                    <td>${c.person ? escapeHtml(c.person.name) : '<span class="ai-muted">Verwijderde gebruiker</span>'}</td>
                    <td>${escapeHtml(c.model)}</td>
                    <td>${aiStatusBadge(c.status)}${c.error_message ? `<div class="ai-error">${escapeHtml(c.error_message)}</div>` : ""}</td>
                    <td class="num">${aiFormatNumber(c.prompt_tokens)}</td>
                    <td class="num">${aiFormatNumber(c.output_tokens)}</td>
                    <td class="num">${aiFormatNumber(c.thinking_tokens)}</td>
                    <td class="num">${aiFormatDuration(c.duration_ms)}</td>
                    <td class="num">${aiFormatEuro(c.cost_eur)}</td>
                    <td>${c.has_content ? '<span class="material-symbols-rounded bp-icon-inline" title="Verzoek en antwoord bewaard">description</span>' : ""}</td>
                </tr>`).join("");
        }
        const first = data.total ? (data.page - 1) * data.page_size + 1 : 0;
        const last = Math.min(data.page * data.page_size, data.total);
        count.textContent = `${first}–${last} van ${data.total}`;
        prev.disabled = data.page <= 1;
        next.disabled = last >= data.total;
    }

    async function openCall(id) {
        try {
            const c = await api(`/api/admin/ai/calls/${id}`);
            const json = value => value === null || value === undefined
                ? '<p class="ai-muted">Niet bewaard (debug-logboek stond uit of de inhoud is gewist).</p>'
                : `<pre class="ai-json">${escapeHtml(typeof value === "string" ? value : JSON.stringify(value, null, 2))}</pre>`;
            aiShowWideModal(`
                <h2>Aanroep #${c.id}</h2>
                <p>${escapeHtml(aiFormatTime(c.created_at))} · ${c.person ? escapeHtml(c.person.name) : "Verwijderde gebruiker"}
                   · ${escapeHtml(c.model)} · ${aiStatusBadge(c.status)}${c.http_status ? ` · HTTP ${c.http_status}` : ""}
                   · ${aiFormatDuration(c.duration_ms)} · ${aiFormatEuro(c.cost_eur)}</p>
                <p class="ai-muted">Tokens: ${aiFormatNumber(c.prompt_tokens)} input (${aiFormatNumber(c.cached_tokens)} uit cache),
                   ${aiFormatNumber(c.output_tokens)} output, ${aiFormatNumber(c.thinking_tokens)} denken</p>
                ${c.error_message ? `<p class="ai-error">${escapeHtml(c.error_message)}</p>` : ""}
                ${c.message_id ? `<p><a href="/admin/ai/log?message_id=${c.message_id}">Alle aanroepen van dit chatbericht</a></p>` : ""}
                <h3>Verzoek</h3>${json(c.request)}
                <h3>Antwoord</h3>${json(c.response)}
                <div class="modal-actions"><button type="button" class="btn" onclick="hideModal()">Sluiten</button></div>
            `);
        } catch (err) {
            showToast("Laden mislukt: " + escapeHtml(err.message), "error");
        }
    }

    rows.addEventListener("click", (e) => {
        const row = e.target.closest("tr[data-id]");
        if (row) openCall(row.dataset.id);
    });
    [person, status, activity, from, to].forEach(el => el.addEventListener("change", () => { page = 1; load(); }));
    document.getElementById("f-reset").addEventListener("click", () => {
        [person, status, activity, from, to].forEach(el => { el.value = ""; });
        page = 1;
        load();
    });
    prev.addEventListener("click", () => { page -= 1; load(); });
    next.addEventListener("click", () => { page += 1; load(); });
    load();
});
