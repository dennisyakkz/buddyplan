package nl.buddyplan.display.data

sealed class SyncResult {
    data class Success(val data: DashboardData) : SyncResult()
    data class Unchanged(val data: DashboardData) : SyncResult()
    object Failed : SyncResult()
    object AuthRequired : SyncResult()
}
