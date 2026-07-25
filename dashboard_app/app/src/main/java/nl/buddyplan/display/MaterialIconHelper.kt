package nl.buddyplan.display

import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.Drawable
import android.os.Build
import android.util.TypedValue
import android.view.Gravity
import android.widget.TextView
import androidx.core.content.ContextCompat

object MaterialIconHelper {

    const val DEFAULT_ICON = "md:check_circle"

    private val legacyMap = mapOf(
        "toothbrush" to "md:dentistry",
        "shower" to "md:shower",
        "food" to "md:restaurant",
        "home" to "md:home",
        "book" to "md:menu_book",
        "music" to "md:music_note",
        "walk" to "md:directions_walk",
        "clothes" to "md:checkroom",
        "water" to "md:water_drop",
        "bed" to "md:bed",
        "check" to DEFAULT_ICON,
        "default" to DEFAULT_ICON,
        "fas:trash" to "custom:kliko-restafval",
        "fas:circle-check" to DEFAULT_ICON,
    )

    private var typeface: Typeface? = null

    fun normalize(iconId: String?): String {
        if (iconId.isNullOrBlank()) return DEFAULT_ICON
        val raw = iconId.trim()
        if (raw.startsWith("md:") || raw.startsWith("custom:")) return raw
        return legacyMap[raw] ?: DEFAULT_ICON
    }

    fun applyIcon(textView: TextView, iconId: String?, sizeSp: Float = 28f) {
        val context = textView.context.applicationContext
        ensureLoaded(context)
        val normalized = normalize(iconId)

        textView.gravity = Gravity.CENTER
        textView.includeFontPadding = false
        textView.setTextColor(ContextCompat.getColor(textView.context, R.color.text_primary))
        textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, sizeSp)
        textView.setCompoundDrawables(null, null, null, null)
        textView.background = null

        if (normalized.startsWith("custom:")) {
            val name = normalized.removePrefix("custom:")
            textView.typeface = Typeface.DEFAULT
            textView.text = ""
            val drawable = loadCustomDrawable(context, name, sizeSp)
            if (drawable != null) {
                textView.setCompoundDrawablesRelative(drawable, null, null, null)
                textView.compoundDrawablePadding = 0
            } else {
                applyMaterialGlyph(textView, "delete")
            }
            return
        }

        val name = normalized.removePrefix("md:")
        applyMaterialGlyph(textView, name)
    }

    private fun applyMaterialGlyph(textView: TextView, name: String) {
        textView.typeface = typeface
        textView.text = name
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            textView.fontVariationSettings = "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
        }
    }

    private fun loadCustomDrawable(context: Context, name: String, sizeSp: Float): Drawable? {
        return try {
            val resId = context.resources.getIdentifier(
                name.replace("-", "_"),
                "drawable",
                context.packageName,
            )
            if (resId != 0) {
                ContextCompat.getDrawable(context, resId)?.mutate()?.also {
                    val sizePx = TypedValue.applyDimension(
                        TypedValue.COMPLEX_UNIT_SP,
                        sizeSp,
                        context.resources.displayMetrics,
                    ).toInt()
                    it.setBounds(0, 0, sizePx, sizePx)
                }
            } else {
                null
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun ensureLoaded(context: Context) {
        if (typeface != null) return
        typeface = Typeface.createFromAsset(context.assets, "fonts/MaterialSymbolsRounded.ttf")
    }
}
