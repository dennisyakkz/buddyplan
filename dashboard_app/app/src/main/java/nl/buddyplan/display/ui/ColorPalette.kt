package nl.buddyplan.display.ui

import android.content.Context
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import kotlin.math.pow

object ColorPalette {

    val LABELS: List<String> = listOf(
        "rood", "oranje", "geel", "groen", "blauw", "teal", "paars", "bruin",
    )

    private val LIGHT_BG = mapOf(
        "rood" to "#FED7D7",
        "oranje" to "#FEEBC8",
        "geel" to "#FEFCBF",
        "groen" to "#C6F6D5",
        "blauw" to "#EBF8FF",
        "teal" to "#E6FFFA",
        "paars" to "#EBF4FF",
        "bruin" to "#EDF2F7",
    )

    private val LIGHT_TEXT = mapOf(
        "rood" to "#9B2C2C",
        "oranje" to "#9C4221",
        "geel" to "#744210",
        "groen" to "#22543D",
        "blauw" to "#2B6CB0",
        "teal" to "#234E52",
        "paars" to "#4C51BF",
        "bruin" to "#4A5568",
    )

    private val DARK_BG = mapOf(
        "rood" to "#9B2C2C",
        "oranje" to "#9C4221",
        "geel" to "#744210",
        "groen" to "#22543D",
        "blauw" to "#2B6CB0",
        "teal" to "#234E52",
        "paars" to "#4C51BF",
        "bruin" to "#4A5568",
    )

    private val DARK_TEXT = mapOf(
        "rood" to "#FFF5F5",
        "oranje" to "#FFFAF0",
        "geel" to "#FFFFF0",
        "groen" to "#F0FFF4",
        "blauw" to "#EBF8FF",
        "teal" to "#E6FFFA",
        "paars" to "#EBF4FF",
        "bruin" to "#F7FAFC",
    )

    private val LEGACY_HEX = mapOf(
        "#e74c3c" to "rood",
        "#e67e22" to "oranje",
        "#f1c40f" to "geel",
        "#27ae60" to "groen",
        "#1abc9c" to "teal",
        "#3498db" to "blauw",
        "#2980b9" to "blauw",
        "#9b59b6" to "paars",
        "#e91e63" to "rood",
        "#795548" to "bruin",
        "#607d8b" to "bruin",
        "#2c3e50" to "bruin",
        "#1e88e5" to "blauw",
        "#43a047" to "groen",
        "#e53935" to "rood",
        "#fb8c00" to "oranje",
        "#8e24aa" to "paars",
        "#00acc1" to "teal",
    )

    fun isDarkMode(context: Context): Boolean {
        val nightMode = context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK
        return nightMode == Configuration.UI_MODE_NIGHT_YES
    }

    fun resolveLabel(color: String?, colorLabel: String? = null): String? {
        val fromLabel = colorLabel?.trim()?.lowercase()
        if (!fromLabel.isNullOrEmpty() && LABELS.contains(fromLabel)) return fromLabel
        return hexToLabel(color)
    }

    fun migrateStoredColor(value: String): String {
        val trimmed = value.trim()
        if (trimmed.isEmpty()) return LABELS.first()
        val lowered = trimmed.lowercase()
        if (LABELS.contains(lowered)) return lowered
        return hexToLabel(trimmed) ?: LABELS.first()
    }

    fun hexToLabel(hex: String?): String? {
        if (hex.isNullOrBlank()) return null
        val raw = hex.trim().lowercase()
        if (LABELS.contains(raw)) return raw
        LEGACY_HEX[raw]?.let { return it }
        if (!raw.startsWith("#") || raw.length != 7) return null
        return LABELS.minByOrNull { label ->
            colorDistance(raw, LIGHT_BG[label] ?: "#FFFFFF")
        }
    }

    fun chipColors(context: Context, label: String): Pair<Int, Int>? {
        val normalized = label.trim().lowercase()
        if (!LABELS.contains(normalized)) return null
        val dark = isDarkMode(context)
        val bgHex = if (dark) DARK_BG[normalized] else LIGHT_BG[normalized]
        val textHex = if (dark) DARK_TEXT[normalized] else LIGHT_TEXT[normalized]
        if (bgHex == null || textHex == null) return null
        return Color.parseColor(bgHex) to Color.parseColor(textHex)
    }

    fun swatchPreviewColor(label: String): Int {
        val normalized = label.trim().lowercase()
        val hex = LIGHT_BG[normalized] ?: "#EDF2F7"
        return Color.parseColor(hex)
    }

    fun chipDrawable(
        context: Context,
        label: String,
        cornerRadiusDp: Float = 12f,
    ): GradientDrawable? {
        val colors = chipColors(context, label) ?: return null
        val radius = cornerRadiusDp * context.resources.displayMetrics.density
        return GradientDrawable().apply {
            shape = GradientDrawable.RECTANGLE
            cornerRadius = radius
            setColor(colors.first)
        }
    }

    private fun colorDistance(a: String, b: String): Double {
        fun rgb(hex: String): Triple<Int, Int, Int> {
            val h = hex.removePrefix("#")
            return Triple(
                h.substring(0, 2).toInt(16),
                h.substring(2, 4).toInt(16),
                h.substring(4, 6).toInt(16),
            )
        }
        val (ar, ag, ab) = rgb(a)
        val (br, bg, bb) = rgb(b)
        return (ar - br).toDouble().pow(2) + (ag - bg).toDouble().pow(2) + (ab - bb).toDouble().pow(2)
    }
}
