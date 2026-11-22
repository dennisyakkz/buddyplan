package nl.buddyplan.display.data

/**
 * Remembers which day the screen marks as today (REQ-DSH-006). The tablet runs for weeks without a
 * restart, and a new day does not always change the dashboard data, so the screen asks this tracker
 * whether its "today" is outdated instead of relying on a data change to redraw.
 */
class DayTracker(private val today: () -> String = WeekDates::todayIso) {

    private var shownDay: String? = null

    /** Call when the screen is drawn; returns the day to mark as today. */
    fun markShown(): String = today().also { shownDay = it }

    /** True when the screen was drawn on an earlier day than the clock's current day. */
    fun isOutdated(): Boolean = shownDay.let { it != null && it != today() }
}
