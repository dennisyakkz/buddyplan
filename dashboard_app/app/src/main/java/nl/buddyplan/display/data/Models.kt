package nl.buddyplan.display.data

data class DashboardData(
    val todo: List<TodoItem>,
    val weekDays: List<WeekDay>,
    val calendar: List<PersonCalendar>
)

data class TodoItem(
    val id: String,
    val title: String,
    val description: String,
    val icon: String,
    var completed: Boolean = false,
    val person_id: Int? = null,
)

data class WeekDay(
    val day: String,
    val date: String,
    val iso: String = ""
)

data class CalendarItem(
    val text: String = "",
    val color: String? = null,
    val title: String? = null,
    val start_time: String? = null,
    val end_time: String? = null,
) {
    fun displayTitle(): String =
        title?.takeIf { it.isNotBlank() } ?: text.trim()

    fun digitalTimeSuffix(): String? {
        val start = start_time?.takeIf { it.isNotBlank() }
        val end = end_time?.takeIf { it.isNotBlank() }
        return when {
            start != null && end != null -> "($start-$end)"
            start != null -> "($start)"
            end != null -> "($end)"
            else -> null
        }
    }

    fun hasStartTime(): Boolean {
        val start = start_time?.takeIf { it.isNotBlank() } ?: return false
        val parts = start.trim().split(":")
        if (parts.size != 2) return false
        return try {
            val hour = parts[0].toInt()
            val minute = parts[1].toInt()
            hour in 0..23 && minute in 0..59
        } catch (_: NumberFormatException) {
            false
        }
    }

    /** Day view: items without time first, then by start time ascending. */
    fun dayViewSortOrder(): Int = if (hasStartTime()) 1 else 0

    fun dayViewSortTime(): String = start_time?.trim().orEmpty()
}

data class DayCalendarEvent(
    val personName: String,
    val item: CalendarItem,
)

data class PersonCalendar(
    val name: String,
    val monday: List<CalendarItem> = emptyList(),
    val tuesday: List<CalendarItem> = emptyList(),
    val wednesday: List<CalendarItem> = emptyList(),
    val thursday: List<CalendarItem> = emptyList(),
    val friday: List<CalendarItem> = emptyList(),
    val saturday: List<CalendarItem> = emptyList(),
    val sunday: List<CalendarItem> = emptyList()
) {
    fun eventsForDay(index: Int): List<CalendarItem> = when (index) {
        0 -> monday
        1 -> tuesday
        2 -> wednesday
        3 -> thursday
        4 -> friday
        5 -> saturday
        6 -> sunday
        else -> emptyList()
    }
}
