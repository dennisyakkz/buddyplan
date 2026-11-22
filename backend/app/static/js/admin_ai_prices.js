// Model prices (REQ-BE-095)
document.addEventListener("DOMContentLoaded", async () => {
    const list = document.getElementById("ai-price-models");
    const form = document.getElementById("ai-price-form");
    const modelInput = document.getElementById("p-model");
    document.getElementById("p-from").value = aiIsoDate(new Date());

    async function load() {
        try {
            render(await api("/api/admin/ai/prices"));
        } catch (err) {
            showToast("Laden mislukt: " + escapeHtml(err.message), "error");
        }
    }

    function render(models) {
        document.getElementById("p-model-list").innerHTML = models
            .map(m => `<option value="${escapeHtml(m.model)}">`).join("");
        if (!models.length) {
            list.innerHTML = '<p class="ai-muted">Nog geen modellen. Stel een model in of voeg hieronder een prijs toe.</p>';
            return;
        }
        list.innerHTML = models.map(m => `
            <h3>${escapeHtml(m.model)}
                ${m.configured ? '<span class="ai-badge ai-badge-ok">ingesteld model</span>' : ""}
                ${m.has_price ? "" : '<span class="ai-badge ai-badge-error">geen prijs</span>'}
            </h3>
            ${m.prices.length ? `
            <div class="ai-table-wrap"><table class="ai-table">
                <thead><tr><th>Geldig vanaf</th><th class="num">Input (€ per 1M)</th><th class="num">Output (€ per 1M)</th><th></th></tr></thead>
                <tbody>${m.prices.map(p => `
                    <tr>
                        <td>${escapeHtml(p.valid_from)}${m.current_price && m.current_price.id === p.id ? ' <span class="ai-muted">(huidig)</span>' : ""}</td>
                        <td class="num">${aiFormatEuro(p.input_price_per_1m)}</td>
                        <td class="num">${aiFormatEuro(p.output_price_per_1m)}</td>
                        <td class="num"><button type="button" class="btn btn-small btn-danger" data-delete="${p.id}">Verwijderen</button></td>
                    </tr>`).join("")}
                </tbody>
            </table></div>` : `<p class="ai-muted"><a href="#" data-add="${escapeHtml(m.model)}">Prijs toevoegen</a></p>`}
        `).join("");
    }

    list.addEventListener("click", async (e) => {
        const add = e.target.closest("[data-add]");
        if (add) {
            e.preventDefault();
            modelInput.value = add.dataset.add;
            document.getElementById("p-input").focus();
            return;
        }
        const del = e.target.closest("[data-delete]");
        if (!del || !confirm("Deze prijs verwijderen? Aanroepen in die periode krijgen dan de vorige prijs of geen prijs.")) return;
        try {
            await api(`/api/admin/ai/prices/${del.dataset.delete}`, { method: "DELETE" });
            showToast("Prijs verwijderd", "success", 3000);
            load();
        } catch (err) {
            showToast("Verwijderen mislukt: " + escapeHtml(err.message), "error");
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            await api("/api/admin/ai/prices", {
                method: "POST",
                body: JSON.stringify({
                    model: modelInput.value.trim(),
                    input_price_per_1m: parseFloat(document.getElementById("p-input").value),
                    output_price_per_1m: parseFloat(document.getElementById("p-output").value),
                    valid_from: document.getElementById("p-from").value,
                }),
            });
            showToast("Prijs toegevoegd", "success", 3000);
            document.getElementById("p-input").value = "";
            document.getElementById("p-output").value = "";
            load();
        } catch (err) {
            showToast("Toevoegen mislukt: " + escapeHtml(err.message), "error");
        }
    });

    load();
});
