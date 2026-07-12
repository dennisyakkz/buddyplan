package nl.buddyplan.display.ui

import android.content.Context
import android.graphics.Typeface
import android.widget.TextView
import androidx.core.content.res.ResourcesCompat
import nl.buddyplan.display.R

object FontHelper {

    fun headingBold(context: Context): Typeface? =
        ResourcesCompat.getFont(context, R.font.plus_jakarta_sans_bold)

    fun headingSemiBold(context: Context): Typeface? =
        ResourcesCompat.getFont(context, R.font.plus_jakarta_sans_semibold)

    fun bodyRegular(context: Context): Typeface? =
        ResourcesCompat.getFont(context, R.font.inter_regular)

    fun bodyMedium(context: Context): Typeface? =
        ResourcesCompat.getFont(context, R.font.inter_medium)

    fun applyHeading(textView: TextView, semiBold: Boolean = false) {
        val typeface = if (semiBold) headingSemiBold(textView.context) else headingBold(textView.context)
        typeface?.let { textView.typeface = it }
    }

    fun applyBody(textView: TextView, medium: Boolean = false) {
        val typeface = if (medium) bodyMedium(textView.context) else bodyRegular(textView.context)
        typeface?.let { textView.typeface = it }
    }
}
