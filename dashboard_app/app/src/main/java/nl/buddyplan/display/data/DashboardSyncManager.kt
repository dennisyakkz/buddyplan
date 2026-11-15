package nl.buddyplan.display.data

import android.content.Context
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.atomic.AtomicBoolean

class DashboardSyncManager(
    context: Context,
    private val scope: CoroutineScope,
    private val weekStartProvider: () -> String,
    private val onUpdated: (DashboardData) -> Unit,
    private val onConnectionState: (ConnectionState) -> Unit,
    private val onAuthRequired: (() -> Unit)? = null,
) {
    private val appContext = context.applicationContext

    private val retryDelaysMs = longArrayOf(
        10_000, 20_000, 40_000, 80_000, 160_000, 300_000,
    )
    // Every poll asks the server for its etag and reloads as soon as it changed; the forced
    // full refresh is only a safety net.
    private val regularIntervalMs = 1 * 60 * 1000L
    private val forceFullRefreshEveryPolls = 10

    private var retryIndex = 0
    private var pollCount = 0
    private var stopped = false
    private var forceNextSync = false
    private var rerunRequested = false
    private val syncInProgress = AtomicBoolean(false)
    private var pollingJob: Job? = null
    private val startMutex = Mutex()

    fun start(force: Boolean = false) {
        scope.launch {
            startMutex.withLock {
                stopped = false
                if (force) retryIndex = 0
                forceNextSync = forceNextSync || force
                if (syncInProgress.get()) {
                    // Let the running sync finish; it starts the next one right away.
                    rerunRequested = true
                    return@withLock
                }
                pollingJob?.cancel()
                performSync()
            }
        }
    }

    fun stop() {
        stopped = true
        pollingJob?.cancel()
        pollingJob = null
    }

    private suspend fun performSync() {
        if (stopped || !syncInProgress.compareAndSet(false, true)) return

        try {
            DataRepository.getCachedDashboard(weekStartProvider())?.let { onUpdated(it) }
            onConnectionState(ConnectionState.Syncing)

            pollCount++
            val force = forceNextSync || (pollCount % forceFullRefreshEveryPolls == 0)
            forceNextSync = false

            val result = DataRepository.syncFromNetwork(
                appContext,
                force,
                weekStartProvider(),
            )

            if (stopped) return

            when (result) {
                is SyncResult.Success -> {
                    retryIndex = 0
                    onUpdated(result.data)
                    onConnectionState(ConnectionState.Connected)
                    scheduleNext(regularIntervalMs)
                }
                is SyncResult.Unchanged -> {
                    retryIndex = 0
                    onUpdated(result.data)
                    onConnectionState(ConnectionState.Connected)
                    scheduleNext(regularIntervalMs)
                }
                is SyncResult.Failed -> {
                    DataRepository.getCachedDashboard(weekStartProvider())?.let { onUpdated(it) }
                    onConnectionState(ConnectionState.Offline)
                    scheduleRetry()
                }
                is SyncResult.AuthRequired -> {
                    DataRepository.getCachedDashboard(weekStartProvider())?.let { onUpdated(it) }
                    onConnectionState(ConnectionState.Offline)
                    onAuthRequired?.invoke()
                    scheduleRetry()
                }
            }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            if (!stopped) {
                DataRepository.getCachedDashboard(weekStartProvider())?.let { onUpdated(it) }
                onConnectionState(ConnectionState.Offline)
                scheduleRetry()
            }
        } finally {
            syncInProgress.set(false)
        }
    }

    private suspend fun scheduleRetry() {
        val delayMs = if (retryIndex < retryDelaysMs.size) {
            retryDelaysMs[retryIndex++]
        } else {
            regularIntervalMs
        }
        scheduleNext(delayMs)
    }

    private fun scheduleNext(delayMs: Long) {
        if (stopped) return
        val effectiveDelayMs = if (rerunRequested) 0L else delayMs
        rerunRequested = false
        pollingJob?.cancel()
        pollingJob = scope.launch {
            delay(effectiveDelayMs)
            if (isActive && !stopped) {
                performSync()
            }
        }
    }
}
