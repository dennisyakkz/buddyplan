package nl.buddyplan.display.data

import java.util.TimeZone
import org.junit.Assert.assertEquals
import org.junit.BeforeClass
import org.junit.Test

class WeekDatesTest {

    companion object {
        @JvmStatic
        @BeforeClass
        fun useTabletTimeZone() {
            // The wall tablet runs in Dutch time; WeekDates' formatter picks this up on first use.
            TimeZone.setDefault(TimeZone.getTimeZone("Europe/Amsterdam"))
        }
    }

    @Test
    fun mondayOfReturnsTheMondayOfThatWeek() {
        assertEquals("2026-11-02", WeekDates.mondayOf("2026-11-02"))
        assertEquals("2026-11-02", WeekDates.mondayOf("2026-11-05"))
        assertEquals("2026-11-02", WeekDates.mondayOf("2026-11-08")) // Sunday belongs to the week before
        assertEquals("2026-12-28", WeekDates.mondayOf("2027-01-01")) // across a year boundary
    }

    @Test
    fun addDaysAndWeeksHandleMonthAndDstBoundaries() {
        assertEquals("2026-12-01", WeekDates.addDays("2026-11-30", 1))
        assertEquals("2026-10-26", WeekDates.addWeeks("2026-10-19", 1)) // DST ends on 2026-10-25
        assertEquals("2026-10-19", WeekDates.addWeeks("2026-11-02", -2))
    }

    @Test
    fun weeksBetweenIsAbsolute() {
        assertEquals(3, WeekDates.weeksBetween("2026-11-02", "2026-11-23"))
        assertEquals(3, WeekDates.weeksBetween("2026-11-23", "2026-11-02"))
        assertEquals(0, WeekDates.weeksBetween("2026-11-02", "2026-11-02"))
    }

    @Test
    fun weeksBetweenCountsWholeWeeksAcrossDstChanges() {
        assertEquals(3, WeekDates.weeksBetween("2026-10-19", "2026-11-09")) // clocks go back on 2026-10-25
        assertEquals(3, WeekDates.weeksBetween("2026-03-16", "2026-04-06")) // clocks go forward on 2026-03-29
    }

    @Test
    fun defaultWindowCoversOneWeekBeforeAndSixAfter() {
        val weeks = WeekDates.defaultWindowWeekStarts("2026-11-02")
        assertEquals(8, weeks.size)
        assertEquals("2026-10-26", weeks.first())
        assertEquals("2026-12-14", weeks.last())
    }

    @Test
    fun dateRangeRunsFromFirstMondayToLastSunday() {
        val range = WeekDates.dateRangeForWeekStarts(listOf("2026-11-16", "2026-11-02", "2026-11-09"))
        assertEquals("2026-11-02" to "2026-11-22", range)
    }
}
