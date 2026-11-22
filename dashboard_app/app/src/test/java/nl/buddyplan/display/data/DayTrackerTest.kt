package nl.buddyplan.display.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** REQ-DSH-006: the screen follows the current day, also without a data change. */
class DayTrackerTest {

    private var clock = "2026-11-21"
    private val tracker = DayTracker { clock }

    @Test
    fun nothingShownYetIsNotOutdated() {
        assertFalse(tracker.isOutdated())
    }

    @Test
    fun sameDayIsNotOutdated() {
        assertEquals("2026-11-21", tracker.markShown())
        assertFalse(tracker.isOutdated())
    }

    @Test
    fun newDayMakesTheScreenOutdatedUntilRedrawn() {
        tracker.markShown()
        clock = "2026-11-22"
        assertTrue(tracker.isOutdated())

        assertEquals("2026-11-22", tracker.markShown())
        assertFalse(tracker.isOutdated())
    }
}
