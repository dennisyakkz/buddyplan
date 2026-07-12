package nl.buddyplan.display

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import nl.buddyplan.display.data.ConnectionState
import nl.buddyplan.display.data.DashboardData
import nl.buddyplan.display.data.DashboardSyncManager
import nl.buddyplan.display.data.DataRepository
import nl.buddyplan.display.data.WeekDates
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class DashboardViewModel(application: Application) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(
        DashboardUiState(currentWeekStart = WeekDates.mondayOfToday()),
    )
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    private var syncManager: DashboardSyncManager? = null
    private var syncStarted = false

    fun initialize() {
        viewModelScope.launch {
            DataRepository.initCache(getApplication())
        }
    }

    fun onResume(isConnectionConfigured: Boolean, settingsOpenedForSetup: Boolean, openSettingsForSetup: () -> Unit) {
        if (!isConnectionConfigured && !settingsOpenedForSetup) {
            openSettingsForSetup()
            return
        }

        viewModelScope.launch {
            DataRepository.initCache(getApplication())
            val weekStart = _uiState.value.currentWeekStart
            val cached = DataRepository.getCachedDashboard(weekStart)
            _uiState.update {
                it.copy(
                    dashboard = cached ?: it.dashboard,
                    hasDisplayedData = cached != null || it.hasDisplayedData,
                    showFullLoading = false,
                    connectionState = if (cached != null) ConnectionState.Offline else it.connectionState,
                )
            }

            if (!syncStarted) {
                syncStarted = true
                startSyncManager()
            } else {
                syncManager?.start(force = !_uiState.value.hasDisplayedData)
            }
        }
    }

    fun forceSync() {
        syncManager?.start(force = true)
    }

    fun navigateWeek(direction: Int) {
        val newWeek = WeekDates.addWeeks(_uiState.value.currentWeekStart, direction)
        setCurrentWeek(newWeek)
    }

    fun goToToday() {
        val todayWeek = WeekDates.mondayOfToday()
        if (_uiState.value.currentWeekStart != todayWeek) {
            setCurrentWeek(todayWeek)
        }
    }

    fun setCurrentWeek(weekStart: String) {
        _uiState.update { it.copy(currentWeekStart = weekStart) }
        viewModelScope.launch {
            val cached = DataRepository.getCachedDashboard(weekStart)
            if (cached != null) {
                _uiState.update { it.copy(dashboard = cached) }
            }
            val data = DataRepository.loadWeek(getApplication(), weekStart)
            if (data != null && _uiState.value.currentWeekStart == weekStart) {
                _uiState.update { it.copy(dashboard = data) }
            }
        }
    }

    fun reportCompletion(taskId: String) {
        viewModelScope.launch {
            DataRepository.reportCompletion(getApplication(), taskId)
        }
    }

    fun clearAuthRequired() {
        _uiState.update { it.copy(authRequired = false) }
    }

    override fun onCleared() {
        syncManager?.stop()
        super.onCleared()
    }

    private fun startSyncManager() {
        syncManager?.stop()
        syncManager = DashboardSyncManager(
            context = getApplication(),
            scope = viewModelScope,
            weekStartProvider = { _uiState.value.currentWeekStart },
            onUpdated = { data ->
                _uiState.update {
                    it.copy(
                        dashboard = data,
                        hasDisplayedData = true,
                        showFullLoading = false,
                    )
                }
            },
            onConnectionState = { state ->
                _uiState.update { it.copy(connectionState = state) }
            },
            onAuthRequired = {
                val app = getApplication<Application>()
                val hadToken = !AppPreferences.getAuthToken(app).isNullOrBlank()
                if (!hadToken) return@DashboardSyncManager
                AppPreferences.setAuthToken(app, null)
                _uiState.update { it.copy(authRequired = true) }
            },
        )
        syncManager?.start(force = !_uiState.value.hasDisplayedData)
    }
}
