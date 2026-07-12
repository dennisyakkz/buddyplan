package nl.buddyplan.display.data

data class DashboardCacheBundle(
    val tasks: List<CachedTaskItem> = emptyList(),
    val weeks: Map<String, WeekCalendarData> = emptyMap(),
)

data class WeekCalendarData(
    val weekDays: List<WeekDay>,
    val calendar: List<PersonCalendar>,
)

data class CachedTaskItem(
    val id: String,
    val title: String,
    val description: String = "",
    val icon: String = "default",
    val completed: Boolean = false,
    val person_id: Int? = null,
    val date: String = "",
)
