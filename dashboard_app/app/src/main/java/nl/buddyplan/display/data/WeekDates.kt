package nl.buddyplan.display.data

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

object WeekDates {

    private val dateFmt = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())

    const val INITIAL_WEEKS_BEFORE = 1
    const val INITIAL_WEEKS_AFTER = 6
    const val PREFETCH_THRESHOLD_WEEKS = 2
    const val PREFETCH_CHUNK_WEEKS = 3

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
        val diffDays = kotlin.math.abs(to - from) / (24L * 60 * 60 * 1000)
        return (diffDays / 7).toInt()
    }

    fun defaultWindowWeekStarts(anchorMonday: String = mondayOfToday()): List<String> {
        return (-INITIAL_WEEKS_BEFORE..INITIAL_WEEKS_AFTER).map { offset ->
            addWeeks(anchorMonday, offset)
        }
    }

    fun dateRangeForWeekStarts(weekStarts: Collection<String>): Pair<String, String> {
        require(weekStarts.isNotEmpty())
        val sorted = weekStarts.sorted()
        val start = sorted.first()
        val end = addDays(sorted.last(), 6)
        return start to end
    }
}
