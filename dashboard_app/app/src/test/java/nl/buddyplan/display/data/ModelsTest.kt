package nl.buddyplan.display.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ModelsTest {

    @Test
    fun displayTitlePrefersTitleOverText() {
        assertEquals("Zwemles", CalendarItem(text = "16:00 Zwemles", title = "Zwemles").displayTitle())
        assertEquals("School: Studiedag", CalendarItem(text = " School: Studiedag ", title = " ").displayTitle())
    }

    @Test
    fun digitalTimeSuffix() {
        assertEquals("(16:00-17:00)", CalendarItem(start_time = "16:00", end_time = "17:00").digitalTimeSuffix())
        assertEquals("(16:00)", CalendarItem(start_time = "16:00").digitalTimeSuffix())
        assertEquals("(17:00)", CalendarItem(start_time = "", end_time = "17:00").digitalTimeSuffix())
        assertNull(CalendarItem().digitalTimeSuffix())
    }

    @Test
    fun hasStartTimeOnlyAcceptsValidClockTimes() {
        assertTrue(CalendarItem(start_time = "09:30").hasStartTime())
        assertTrue(CalendarItem(start_time = " 0:00 ").hasStartTime())
        assertFalse(CalendarItem(start_time = "24:00").hasStartTime())
        assertFalse(CalendarItem(start_time = "9.30").hasStartTime())
        assertFalse(CalendarItem(start_time = "aa:bb").hasStartTime())
        assertFalse(CalendarItem().hasStartTime())
    }

    @Test
    fun dayViewSortsAllDayItemsFirstThenByTime() {
        val items = listOf(
            CalendarItem(title = "Tandarts", start_time = "14:00"),
            CalendarItem(title = "Studiedag"),
            CalendarItem(title = "Zwemles", start_time = "09:00"),
        )
        val sorted = items.sortedWith(compareBy({ it.dayViewSortOrder() }, { it.dayViewSortTime() }))
        assertEquals(listOf("Studiedag", "Zwemles", "Tandarts"), sorted.map { it.displayTitle() })
    }

    @Test
    fun eventsForDayMapsIndexToWeekday() {
        val wednesday = listOf(CalendarItem(title = "Muziekles"))
        val calendar = PersonCalendar(name = "Fiona", wednesday = wednesday)
        assertEquals(wednesday, calendar.eventsForDay(2))
        assertTrue(calendar.eventsForDay(0).isEmpty())
        assertTrue(calendar.eventsForDay(7).isEmpty())
    }
}
