package nl.buddyplan.display

import android.content.Context

/**
 * Persists dashboard APK install progress across activity/process restarts.
 * Only reports "in progress" while a known install session is active and not timed out.
 */
object UpgradeInstallState {

    enum class Phase {
        NONE,
        AWAITING_CONFIRM,
        INSTALLING,
    }

    private const val KEY_PHASE = "upgrade_install_phase"
    private const val KEY_STARTED_AT = "upgrade_install_started_at"

    private const val AWAITING_CONFIRM_TIMEOUT_MS = 3 * 60 * 1000L
    private const val INSTALLING_TIMEOUT_MS = 5 * 60 * 1000L

    fun markAwaitingConfirm(context: Context) {
        prefs(context).edit()
            .putString(KEY_PHASE, Phase.AWAITING_CONFIRM.name)
            .putLong(KEY_STARTED_AT, System.currentTimeMillis())
            .apply()
    }

    fun markInstalling(context: Context) {
        prefs(context).edit()
            .putString(KEY_PHASE, Phase.INSTALLING.name)
            .putLong(KEY_STARTED_AT, System.currentTimeMillis())
            .apply()
    }

    fun clear(context: Context) {
        prefs(context).edit()
            .remove(KEY_PHASE)
            .remove(KEY_STARTED_AT)
            .apply()
    }

    fun getPhase(context: Context): Phase {
        reconcile(context)
        val raw = prefs(context).getString(KEY_PHASE, null) ?: return Phase.NONE
        return runCatching { Phase.valueOf(raw) }.getOrDefault(Phase.NONE)
    }

    fun isInProgress(context: Context): Boolean {
        val phase = getPhase(context)
        return phase == Phase.AWAITING_CONFIRM || phase == Phase.INSTALLING
    }

    fun isInstalling(context: Context): Boolean =
        getPhase(context) == Phase.INSTALLING

    /** Clears stale install state when the deadline has passed. */
    fun reconcile(context: Context) {
        val phase = readPhaseRaw(context) ?: return
        val startedAt = prefs(context).getLong(KEY_STARTED_AT, 0L)
        if (startedAt <= 0L || System.currentTimeMillis() - startedAt > timeoutFor(phase)) {
            clear(context)
        }
    }

    fun getDeadlineMs(context: Context): Long? {
        val phase = readPhaseRaw(context) ?: return null
        val startedAt = prefs(context).getLong(KEY_STARTED_AT, 0L)
        if (startedAt <= 0L) return null
        return startedAt + timeoutFor(phase)
    }

    private fun readPhaseRaw(context: Context): Phase? {
        val raw = prefs(context).getString(KEY_PHASE, null) ?: return null
        return runCatching { Phase.valueOf(raw) }.getOrNull()
    }

    private fun timeoutFor(phase: Phase): Long = when (phase) {
        Phase.AWAITING_CONFIRM -> AWAITING_CONFIRM_TIMEOUT_MS
        Phase.INSTALLING -> INSTALLING_TIMEOUT_MS
        Phase.NONE -> 0L
    }

    private fun prefs(context: Context) =
        context.applicationContext.getSharedPreferences(AppPreferences.PREFS_NAME, Context.MODE_PRIVATE)

}
