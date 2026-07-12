package nl.buddyplan.display.ui

import android.content.Context
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.LayoutInflater
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import nl.buddyplan.display.R
import nl.buddyplan.display.data.CalendarItem
import nl.buddyplan.display.data.PersonCalendar
import nl.buddyplan.display.data.WeekDay

object CalendarViewBuilder {

    private const val NAME_COLUMN_WEIGHT = 0.8f
    private const val DAY_COLUMN_WEIGHT = 1f

    fun build(
        context: Context,
        container: LinearLayout,
        weekDays: List<WeekDay>,
        people: List<PersonCalendar>,
        todayIso: String = "",
        onDayHeaderClick: ((Int, WeekDay) -> Unit)? = null,
        onPersonDayClick: ((Int, WeekDay, PersonCalendar) -> Unit)? = null,
    ) {
        container.removeAllViews()
        container.addView(buildHeaderRow(context, weekDays, todayIso, onDayHeaderClick))
        people.forEach { person ->
            container.addView(buildPersonRow(context, weekDays, person, todayIso, onPersonDayClick))
        }
    }

    private fun buildHeaderRow(
        context: Context,
        weekDays: List<WeekDay>,
        todayIso: String,
        onDayHeaderClick: ((Int, WeekDay) -> Unit)?,
    ): LinearLayout {
        val row = createRow(context)
        row.addView(createNameCell(context, "", isHeader = true))

        weekDays.forEachIndexed { dayIndex, weekDay ->
            val isToday = todayIso.isNotEmpty() && weekDay.iso == todayIso
            val cell = LayoutInflater.from(context)
                .inflate(R.layout.item_calendar_header, row, false) as LinearLayout
            cell.layoutParams = createCellParams(DAY_COLUMN_WEIGHT)
            cell.setBackgroundResource(
                if (isToday) R.drawable.calendar_today_header_background
                else R.drawable.calendar_header_background
            )

            val dayNameView = cell.findViewById<TextView>(R.id.dayName)
            val dayDateView = cell.findViewById<TextView>(R.id.dayDate)
            dayNameView.text = weekDay.day
            dayDateView.text = weekDay.date

            if (isToday) {
                val todayText = ContextCompat.getColor(context, R.color.calendar_today_header_text)
                dayNameView.setTextColor(todayText)
                dayDateView.setTextColor(todayText)
            }

            if (onDayHeaderClick != null) {
                cell.isClickable = true
                cell.isFocusable = true
                cell.foreground = selectableForeground(context)
                cell.setOnClickListener { onDayHeaderClick(dayIndex, weekDay) }
            }

            row.addView(cell)
        }
        return row
    }

    private fun buildPersonRow(
        context: Context,
        weekDays: List<WeekDay>,
        person: PersonCalendar,
        todayIso: String,
        onPersonDayClick: ((Int, WeekDay, PersonCalendar) -> Unit)?,
    ): LinearLayout {
        val row = createRow(context)
        row.addView(createNameCell(context, person.name, isHeader = false))

        weekDays.forEachIndexed { dayIndex, weekDay ->
            val isToday = todayIso.isNotEmpty() && weekDay.iso == todayIso
            val events = person.eventsForDay(dayIndex)

            val cell = LinearLayout(context).apply {
                layoutParams = createCellParams(DAY_COLUMN_WEIGHT)
                orientation = LinearLayout.VERTICAL
                setPadding(dp(context, 4), dp(context, 4), dp(context, 4), dp(context, 4))
                setBackgroundResource(
                    if (isToday) R.drawable.calendar_today_cell_background
                    else R.drawable.calendar_cell_background
                )
            }

            events.forEach { item ->
                cell.addView(createChip(context, item))
            }

            if (onPersonDayClick != null) {
                cell.isClickable = true
                cell.isFocusable = true
                cell.foreground = selectableForeground(context)
                cell.setOnClickListener { onPersonDayClick(dayIndex, weekDay, person) }
            }

            row.addView(cell)
        }
        return row
    }

    private fun createChip(context: Context, item: CalendarItem): TextView {
        val label = ColorPalette.resolveLabel(item.color, item.color_label)
        return TextView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).also { it.setMargins(0, 0, 0, dp(context, 2)) }
            text = item.text
            textSize = 14f
            setPadding(dp(context, 6), dp(context, 4), dp(context, 6), dp(context, 4))
            FontHelper.applyBody(this)

            if (label != null) {
                val colors = ColorPalette.chipColors(context, label)
                if (colors != null) {
                    background = ColorPalette.chipDrawable(context, label, 12f)
                    setTextColor(colors.second)
                } else {
                    setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
                }
            } else {
                text = "• ${item.text}"
                setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
            }
        }
    }

    private fun createRow(context: Context): LinearLayout {
        return LinearLayout(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
            orientation = LinearLayout.HORIZONTAL
        }
    }

    private fun createNameCell(context: Context, name: String, isHeader: Boolean): TextView {
        return TextView(context).apply {
            layoutParams = createCellParams(NAME_COLUMN_WEIGHT)
            text = name
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(context, 8), dp(context, 4), dp(context, 8), dp(context, 4))
            if (isHeader) {
                setBackgroundResource(R.drawable.calendar_header_background)
                textSize = 16f
                FontHelper.applyHeading(this, semiBold = true)
                setTextColor(ContextCompat.getColor(context, R.color.text_primary))
            } else {
                setBackgroundResource(R.drawable.calendar_name_background)
                setTextAppearance(context, R.style.CalendarPersonName)
            }
        }
    }

    private fun createCellParams(weight: Float): LinearLayout.LayoutParams {
        return LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, weight)
    }

    private fun dp(context: Context, value: Int): Int {
        return (value * context.resources.displayMetrics.density).toInt()
    }

    private fun selectableForeground(context: Context): android.graphics.drawable.Drawable? {
        val typedValue = android.util.TypedValue()
        return if (context.theme.resolveAttribute(android.R.attr.selectableItemBackground, typedValue, true)) {
            ContextCompat.getDrawable(context, typedValue.resourceId)
        } else {
            null
        }
    }
}
