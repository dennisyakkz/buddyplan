const COLOR_LABELS = ["rood", "oranje", "geel", "groen", "blauw", "teal", "paars", "bruin"];

const COLOR_SWATCHES = [
    { label: "rood", name: "Rood", bg: "#FED7D7", text: "#9B2C2C" },
    { label: "oranje", name: "Oranje", bg: "#FEEBC8", text: "#9C4221" },
    { label: "geel", name: "Geel", bg: "#FEFCBF", text: "#744210" },
    { label: "groen", name: "Groen", bg: "#C6F6D5", text: "#22543D" },
    { label: "blauw", name: "Blauw", bg: "#EBF8FF", text: "#2B6CB0" },
    { label: "teal", name: "Teal", bg: "#E6FFFA", text: "#234E52" },
    { label: "paars", name: "Paars", bg: "#EBF4FF", text: "#4C51BF" },
    { label: "bruin", name: "Bruin", bg: "#EDF2F7", text: "#4A5568" },
];

const LEGACY_HEX_MAP = {
    "#e74c3c": "rood",
    "#e67e22": "oranje",
    "#f1c40f": "geel",
    "#27ae60": "groen",
    "#1abc9c": "teal",
    "#3498db": "blauw",
    "#2980b9": "blauw",
    "#9b59b6": "paars",
    "#e91e63": "rood",
    "#795548": "bruin",
    "#607d8b": "bruin",
    "#2c3e50": "bruin",
};

function normalizeColorLabel(value) {
    if (!value) return "";
    const raw = String(value).trim().toLowerCase();
    if (COLOR_LABELS.includes(raw)) return raw;
    if (LEGACY_HEX_MAP[raw]) return LEGACY_HEX_MAP[raw];
    if (/^#[0-9a-f]{6}$/i.test(raw)) {
        let best = "";
        let bestDist = Infinity;
        for (const swatch of COLOR_SWATCHES) {
            const dist = colorDistance(raw, swatch.bg);
            if (dist < bestDist) {
                bestDist = dist;
                best = swatch.label;
            }
        }
        return best;
    }
    return "";
}

function colorDistance(hexA, hexB) {
    const a = hexToRgb(hexA);
    const b = hexToRgb(hexB);
    return (a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2;
}

function hexToRgb(hex) {
    const h = hex.replace("#", "");
    return {
        r: parseInt(h.slice(0, 2), 16),
        g: parseInt(h.slice(2, 4), 16),
        b: parseInt(h.slice(4, 6), 16),
    };
}

function badgeClasses(label) {
    const normalized = normalizeColorLabel(label);
    if (!normalized) return "cal-chip";
    return `cal-chip agenda-badge-${normalized}`;
}

function badgeHtml(label, text) {
    const cls = badgeClasses(label);
    return `<span class="${cls}">${text}</span>`;
}

function buildColorSwatches(selectedColor) {
    const normalized = normalizeColorLabel(selectedColor);
    const noneSelected = !normalized;
    const swatches = COLOR_SWATCHES.map((c) =>
        `<button type="button" class="color-swatch${normalized === c.label ? " selected" : ""}" data-color="${c.label}" title="${c.name}" style="background:${c.bg};color:${c.text}"></button>`
    ).join("");
    return `<button type="button" class="color-swatch swatch-none${noneSelected ? " selected" : ""}" data-color="" title="Geen kleur">✕</button>${swatches}`;
}
