package nl.buddyplan.display.data

import java.util.TimeZone
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
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

    @Test
    fun chunksFitTheBackendRangeLimit() {
        // 16 consecutive weeks: one request may cover at most 12 weeks (83 days).
        val weeks = (0 until 16).map { WeekDates.addWeeks("2026-09-07", it) }.shuffled()
        val chunks = WeekDates.chunkWeekStarts(weeks)
        assertEquals(listOf(12, 4), chunks.map { it.size })
        assertEquals(weeks.sorted(), chunks.flatten())
        for (chunk in chunks) {
            val (start, end) = WeekDates.dateRangeForWeekStarts(chunk)
            assertTrue(WeekDates.weeksBetween(start, WeekDates.mondayOf(end)) < WeekDates.MAX_REQUEST_WEEKS)
        }
    }

    @Test
    fun chunksSplitOnGapsAndDropDuplicates() {
        val chunks = WeekDates.chunkWeekStarts(listOf("2026-11-02", "2027-03-01", "2026-11-02", "2026-11-09"))
        assertEquals(listOf(listOf("2026-11-02", "2026-11-09"), listOf("2027-03-01")), chunks)
        assertTrue(WeekDates.chunkWeekStarts(emptyList()).isEmpty())
    }

    @Test
    fun keepsWeeksNearTodayOrTheViewedWeek() {
        val today = "2026-11-16"
        assertTrue(WeekDates.shouldKeepWeek("2026-09-21", today, today)) // 8 weeks back
        assertFalse(WeekDates.shouldKeepWeek("2026-09-14", today, today)) // 9 weeks back
        assertTrue(WeekDates.shouldKeepWeek("2027-01-11", today, today)) // 8 weeks ahead
        assertFalse(WeekDates.shouldKeepWeek("2027-02-15", today, today))
        assertTrue(WeekDates.shouldKeepWeek("2027-02-15", today, "2027-03-01")) // near the viewed week
    }
}
