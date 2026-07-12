package nl.buddyplan.display

import android.content.Context
import android.graphics.Typeface
import android.view.Gravity
import android.widget.TextView
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

object FaIconHelper {

    private val legacyMap = mapOf(
        "toothbrush" to "tooth",
        "shower" to "shower",
        "food" to "utensils",
        "home" to "house",
        "book" to "book",
        "music" to "music",
        "walk" to "person-walking",
        "clothes" to "shirt",
        "water" to "glass-water",
        "bed" to "bed",
        "default" to "circle-check",
    )

    private var unicodeMap: Map<String, String>? = null
    private var typeface: Typeface? = null

    fun applyIcon(textView: TextView, iconId: String?, sizeSp: Float = 28f) {
        val context = textView.context.applicationContext
        ensureLoaded(context)

        val hex = unicodeMap?.get(resolveName(iconId)) ?: unicodeMap?.get("circle-check") ?: "f058"
        val codePoint = hex.toInt(16)

        textView.typeface = typeface
        textView.text = String(Character.toChars(codePoint))
        textView.textSize = sizeSp
        textView.setTextColor(ContextCompat.getColor(textView.context, R.color.text_primary))
        textView.gravity = Gravity.CENTER
        textView.includeFontPadding = false
    }

    private fun ensureLoaded(context: Context) {
        if (typeface == null) {
            typeface = Typeface.createFromAsset(context.assets, "fonts/fa-solid-900.ttf")
        }
        if (unicodeMap == null) {
            val json = context.assets.open("fa-unicode-map.json").bufferedReader().readText()
            val type = object : TypeToken<Map<String, String>>() {}.type
            unicodeMap = Gson().fromJson(json, type)
        }
    }

    private fun resolveName(iconId: String?): String {
        if (iconId.isNullOrBlank()) return legacyMap["default"]!!
        if (iconId.startsWith("fas:")) return iconId.removePrefix("fas:")
        return legacyMap[iconId] ?: iconId
    }
}
