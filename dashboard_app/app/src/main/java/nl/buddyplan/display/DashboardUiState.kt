package nl.buddyplan.display

import nl.buddyplan.display.data.ConnectionState
import nl.buddyplan.display.data.DashboardData

data class DashboardUiState(
    val dashboard: DashboardData? = null,
    val connectionState: ConnectionState = ConnectionState.Offline,
    val currentWeekStart: String = "",
    val hasDisplayedData: Boolean = false,
    val showFullLoading: Boolean = false,
    val authRequired: Boolean = false,
)
