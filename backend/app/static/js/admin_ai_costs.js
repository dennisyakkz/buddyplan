// Cost overview (REQ-BE-097)
document.addEventListener("DOMContentLoaded", () => {
    const from = document.getElementById("c-from");
    const to = document.getElementById("c-to");

    function setMonth() {
        const now = new Date();
        from.value = aiIsoDate(new Date(now.getFullYear(), now.getMonth(), 1));
        to.value = aiIsoDate(new Date(now.getFullYear(), now.getMonth() + 1, 0));
    }

    function stat(label, value) {
        return `<div class="ai-stat"><div class="ai-stat-label">${escapeHtml(label)}</div><div class="ai-stat-value">${escapeHtml(value)}</div></div>`;
    }

    function table(el, firstHeader, rows, extraHeader, extraCell) {
        if (!rows.length) {
            el.innerHTML = '<tbody><tr><td class="ai-muted">Geen aanroepen in deze periode.</td></tr></tbody>';
            return;
        }
        el.innerHTML = `
            <thead><tr><th>${firstHeader}</th>${extraHeader ? `<th>${extraHeader}</th>` : ""}
                <th class="num">Aanroepen</th><th class="num">Input</th><th class="num">Output</th><th class="num">Denken</th><th class="num">Kosten</th></tr></thead>
            <tbody>${rows.map(r => `
                <tr><td>${escapeHtml(r.label)}</td>${extraHeader ? `<td>${extraCell(r)}</td>` : ""}
                    <td class="num">${aiFormatNumber(r.calls)}</td>
                    <td class="num">${aiFormatNumber(r.prompt_tokens)}</td>
                    <td class="num">${aiFormatNumber(r.output_tokens)}</td>
                    <td class="num">${aiFormatNumber(r.thinking_tokens)}</td>
                    <td class="num">${aiFormatUsd(r.cost_eur)}${r.unpriced_calls ? ` <span class="ai-muted">(+${r.unpriced_calls} zonder prijs)</span>` : ""}</td>
                </tr>`).join("")}</tbody>`;
    }

    function render(data) {
        const s = data.summary;
        document.getElementById("ai-cost-stats").innerHTML = [
            stat("Totale kosten", aiFormatUsd(s.cost_eur)),
            stat("Aanroepen", aiFormatNumber(s.calls)),
            stat("Input-tokens", aiFormatNumber(s.prompt_tokens)),
            stat("Output-tokens", aiFormatNumber(s.output_tokens)),
            stat("Denk-tokens", aiFormatNumber(s.thinking_tokens)),
            stat("Actieve gebruikers", aiFormatNumber(s.active_users)),
            stat("Gemiddeld per gebruiker", aiFormatUsd(s.avg_cost_per_user)),
        ].join("");

        const unpriced = document.getElementById("ai-cost-unpriced");
        if (s.unpriced_calls) {
            unpriced.classList.remove("hidden");
            unpriced.innerHTML = `${aiFormatNumber(s.unpriced_calls)} aanroepen hebben geen prijs en tellen als $ 0. Voeg de prijs toe op <a href="/admin/ai/prices">AI-prijzen</a>.`;
        } else {
            unpriced.classList.add("hidden");
        }

        const days = data.by_day;
        const max = Math.max(0, ...days.map(d => d.cost_eur));
        document.getElementById("ai-cost-days").innerHTML = days.map(d => {
            const height = max > 0 ? Math.max(1, Math.round((d.cost_eur / max) * 100)) : 1;
            const title = `${d.date}: ${aiFormatUsd(d.cost_eur)}, ${d.calls} aanroepen${d.unpriced_calls ? `, ${d.unpriced_calls} zonder prijs` : ""}`;
            return `<div class="bar${d.cost_eur > 0 ? "" : " zero"}" style="height:${height}%" title="${escapeHtml(title)}"></div>`;
        }).join("");
        document.getElementById("ai-cost-day-first").textContent = days.length ? days[0].date : "";
        document.getElementById("ai-cost-day-last").textContent = days.length ? days[days.length - 1].date : "";

        table(document.getElementById("ai-cost-users"), "Gebruiker", data.by_user.map(r => ({ ...r, label: r.name })));
        table(document.getElementById("ai-cost-models"), "Model", data.by_model.map(r => ({ ...r, label: r.model })),
            "Huidige prijs (in / uit per 1M)",
            r => r.current_price
                ? `${aiFormatUsd(r.current_price.input_price_per_1m)} / ${aiFormatUsd(r.current_price.output_price_per_1m)}`
                : '<span class="ai-badge ai-badge-error">geen prijs</span>');
        table(document.getElementById("ai-cost-activities"), "Activiteit", data.by_activity.map(r => ({ ...r, label: r.activity })));
    }

    async function load() {
        const params = new URLSearchParams();
        if (from.value) params.set("date_from", from.value);
        if (to.value) params.set("date_to", to.value);
        try {
            render(await api(`/api/admin/ai/costs?${params}`));
        } catch (err) {
            showToast("Laden mislukt: " + escapeHtml(err.message), "error");
        }
    }

    from.addEventListener("change", load);
    to.addEventListener("change", load);
    document.getElementById("c-month").addEventListener("click", () => { setMonth(); load(); });
    setMonth();
    load();
});
