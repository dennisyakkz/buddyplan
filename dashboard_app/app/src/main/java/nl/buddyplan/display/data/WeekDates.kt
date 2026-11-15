package nl.buddyplan.display.data

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

object WeekDates {

    // SimpleDateFormat is not thread-safe and WeekDates is used from the UI and IO threads.
    private val dateFmtLocal = object : ThreadLocal<SimpleDateFormat>() {
        override fun initialValue() = SimpleDateFormat("yyyy-MM-dd", Locale.US)
    }
    private val dateFmt: SimpleDateFormat
        get() = dateFmtLocal.get()!!

    const val INITIAL_WEEKS_BEFORE = 1
    const val INITIAL_WEEKS_AFTER = 6
    const val PREFETCH_THRESHOLD_WEEKS = 2
    const val PREFETCH_CHUNK_WEEKS = 3

    /** GET /api/dashboard rejects ranges longer than 12 weeks (83 days). */
    const val MAX_REQUEST_WEEKS = 12

    /** Cached weeks further than this from today and from the viewed week are dropped. */
    const val KEEP_WEEKS_AROUND_TODAY = 8
    const val KEEP_WEEKS_AROUND_VIEW = 4

    fun todayIso(): String = dateFmt.format(Calendar.getInstance().time)

    fun mondayOf(isoDate: String): String {
        val cal = Calendar.getInstance()
        cal.time = dateFmt.parse(isoDate)!!
        val daysFromMonday = (cal.get(Calendar.DAY_OF_WEEK) + 5) % 7
        cal.add(Calendar.DAY_OF_MONTH, -daysFromMonday)
        return dateFmt.format(cal.time)
    }

    fun mondayOfToday(): String = mondayOf(todayIso())

    fun addDays(isoDate: String, days: Int): String {
        val cal = Calendar.getInstance()
        cal.time = dateFmt.parse(isoDate)!!
        cal.add(Calendar.DAY_OF_MONTH, days)
        return dateFmt.format(cal.time)
    }

    fun addWeeks(mondayIso: String, weeks: Int): String =
        addDays(mondayIso, weeks * 7)

    /** Absolute week distance between two Monday ISO dates. */
    fun weeksBetween(fromMonday: String, toMonday: String): Int {
        val from = dateFmt.parse(fromMonday)!!.time
        val to = dateFmt.parse(toMonday)!!.time
        // Round instead of truncating: a DST change makes a day 23 or 25 hours long.
        val diffDays = Math.round(kotlin.math.abs(to - from) / (24.0 * 60 * 60 * 1000))
        return (diffDays / 7).toInt()
    }

    fun defaultWindowWeekStarts(anchorMonday: String = mondayOfToday()): List<String> {
        return (-INITIAL_WEEKS_BEFORE..INITIAL_WEEKS_AFTER).map { offset ->
            addWeeks(anchorMonday, offset)
        }
    }

    /** Splits Monday dates into sorted groups that each fit in one dashboard request. */
    fun chunkWeekStarts(
        weekStarts: Collection<String>,
        maxWeeks: Int = MAX_REQUEST_WEEKS,
    ): List<List<String>> {
        val chunks = mutableListOf<MutableList<String>>()
        for (week in weekStarts.distinct().sorted()) {
            val current = chunks.lastOrNull()
            if (current != null && weeksBetween(current.first(), week) < maxWeeks) {
                current.add(week)
            } else {
                chunks.add(mutableListOf(week))
            }
        }
        return chunks
    }

    /** Whether a cached week is still worth keeping (and refreshing). */
    fun shouldKeepWeek(weekStart: String, todayMonday: String, viewWeekStart: String): Boolean =
        weeksBetween(weekStart, todayMonday) <= KEEP_WEEKS_AROUND_TODAY ||
            weeksBetween(weekStart, viewWeekStart) <= KEEP_WEEKS_AROUND_VIEW

    fun dateRangeForWeekStarts(weekStarts: Collection<String>): Pair<String, String> {
        require(weekStarts.isNotEmpty())
        val sorted = weekStarts.sorted()
        val start = sorted.first()
        val end = addDays(sorted.last(), 6)
        return start to end
    }
}
