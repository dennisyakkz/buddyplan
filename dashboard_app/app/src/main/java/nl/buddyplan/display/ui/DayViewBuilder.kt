package nl.buddyplan.display.ui

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.content.ContextCompat
import nl.buddyplan.display.R
import nl.buddyplan.display.data.DayCalendarEvent
import nl.buddyplan.display.data.WeekDay
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

object DayViewBuilder {

    fun formatDayHeader(weekDay: WeekDay): String {
        if (weekDay.iso.isNotBlank()) {
            try {
                val parts = weekDay.iso.split("-")
                if (parts.size == 3) {
                    val cal = Calendar.getInstance()
                    cal.set(parts[0].toInt(), parts[1].toInt() - 1, parts[2].toInt())
                    val formatted = SimpleDateFormat("EEEE d MMMM", Locale("nl", "NL")).format(cal.time)
                    return formatted.substring(0, 1).uppercase(Locale("nl", "NL")) + formatted.substring(1)
                }
            } catch (_: Exception) {
                // fall through
            }
        }
        return "${weekDay.day} ${weekDay.date}"
    }

    fun buildList(
        context: Context,
        container: LinearLayout,
        events: List<DayCalendarEvent>,
    ) {
        container.removeAllViews()
        if (events.isEmpty()) {
            container.addView(TextView(context).apply {
                text = "Geen items"
                textSize = 18f
                gravity = Gravity.CENTER
                setPadding(dp(context, 24), dp(context, 48), dp(context, 24), dp(context, 24))
                setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
            })
            return
        }

        events.forEachIndexed { index, event ->
            if (index > 0) {
                container.addView(divider(context))
            }
            container.addView(buildEventRow(context, event))
        }
    }

    fun wrapInScrollView(context: Context, content: LinearLayout): ScrollView {
        return ScrollView(context).apply {
            addView(content)
        }
    }

    private fun buildEventRow(context: Context, event: DayCalendarEvent): LinearLayout {
        val clockSize = dp(context, 96)
        val clockMarginEnd = dp(context, 16)
        val rowVerticalPadding = dp(context, 14)
        val clockSlotParams = LinearLayout.LayoutParams(clockSize, clockSize).also {
            it.marginEnd = clockMarginEnd
        }

        val row = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = clockSize + rowVerticalPadding * 2
            setPadding(dp(context, 16), rowVerticalPadding, dp(context, 16), rowVerticalPadding)
        }

        if (event.item.hasStartTime()) {
            row.addView(AnalogClockView(context).apply {
                time = event.item.start_time
                layoutParams = clockSlotParams
            })
        } else {
            row.addView(android.view.View(context).apply {
                layoutParams = clockSlotParams
            })
        }

        val personName = TextView(context).apply {
            text = event.personName
            textSize = 16f
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LinearLayout.LayoutParams(
                dp(context, 120),
                LinearLayout.LayoutParams.WRAP_CONTENT,
            ).also { it.marginEnd = dp(context, 16) }
        }
        row.addView(personName)

        val textColumn = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            gravity = Gravity.CENTER_VERTICAL
        }

        val titleView = TextView(context).apply {
            text = event.item.displayTitle()
            textSize = 22f
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(ContextCompat.getColor(context, R.color.text_primary))
        }
        textColumn.addView(titleView)

        event.item.digitalTimeSuffix()?.let { suffix ->
            textColumn.addView(TextView(context).apply {
                text = " $suffix"
                textSize = 14f
                setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
            })
        }

        row.addView(textColumn)

        parseColor(event.item.color)?.let { color ->
            row.setBackgroundColor(Color.argb(24, Color.red(color), Color.green(color), Color.blue(color)))
        }

        return row
    }

    private fun divider(context: Context) = android.view.View(context).apply {
        layoutParams = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(context, 1),
        )
        setBackgroundColor(ContextCompat.getColor(context, R.color.divider))
    }

    private fun parseColor(hex: String?): Int? {
        if (hex.isNullOrBlank() || !hex.startsWith("#")) return null
        return try {
            Color.parseColor(hex)
        } catch (_: IllegalArgumentException) {
            null
        }
    }

    private fun dp(context: Context, value: Int): Int =
        (value * context.resources.displayMetrics.density).toInt()
}
