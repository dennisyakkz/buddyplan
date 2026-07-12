package nl.buddyplan.display

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import nl.buddyplan.display.ui.ColorPalette

object AppPreferences {

    internal const val PREFS_NAME = "buddyplan_prefs"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_AUTH_TOKEN = "auth_token"
    private const val KEY_LOGGED_IN_NAME = "logged_in_name"
    private const val KEY_PIN_ENABLED = "pin_enabled"
    private const val KEY_PIN_CODE = "pin_code"
    private const val KEY_USER_ENABLED = "user_enabled"
    private const val KEY_USER_COLORS = "user_colors"
    private const val KEY_DARK_MODE = "dark_mode"

    private val gson = Gson()

    val DEFAULT_LABELS = ColorPalette.LABELS

    fun getServerUrl(context: Context): String =
        prefs(context).getString(KEY_SERVER_URL, "")?.trimEnd('/') ?: ""

    fun setServerUrl(context: Context, url: String) {
        prefs(context).edit().putString(KEY_SERVER_URL, url.trimEnd('/')).apply()
    }

    fun getAuthToken(context: Context): String? =
        prefs(context).getString(KEY_AUTH_TOKEN, null)

    fun setAuthToken(context: Context, token: String?) {
        val editor = prefs(context).edit()
        if (token == null) {
            editor.remove(KEY_AUTH_TOKEN)
        } else {
            editor.putString(KEY_AUTH_TOKEN, token)
        }
        editor.commit()
    }

    fun getLoggedInName(context: Context): String? =
        prefs(context).getString(KEY_LOGGED_IN_NAME, null)

    fun setLoggedInName(context: Context, name: String?) {
        if (name == null) {
            prefs(context).edit().remove(KEY_LOGGED_IN_NAME).apply()
        } else {
            prefs(context).edit().putString(KEY_LOGGED_IN_NAME, name).apply()
        }
    }

    fun getDeviceId(context: Context): String {
        val stored = prefs(context).getString(KEY_DEVICE_ID, null)
        if (!stored.isNullOrBlank()) return stored
        val generated = java.util.UUID.randomUUID().toString()
        prefs(context).edit().putString(KEY_DEVICE_ID, generated).apply()
        return generated
    }

    fun isPinEnabled(context: Context): Boolean =
        prefs(context).getBoolean(KEY_PIN_ENABLED, false)

    fun setPinEnabled(context: Context, enabled: Boolean) {
        prefs(context).edit().putBoolean(KEY_PIN_ENABLED, enabled).apply()
    }

    fun getPinCode(context: Context): String =
        prefs(context).getString(KEY_PIN_CODE, "") ?: ""

    fun setPinCode(context: Context, pin: String) {
        prefs(context).edit().putString(KEY_PIN_CODE, pin).apply()
    }

    fun getUserEnabled(context: Context): Map<Int, Boolean> {
        val json = prefs(context).getString(KEY_USER_ENABLED, null) ?: return emptyMap()
        return try {
            val type = object : TypeToken<Map<String, Boolean>>() {}.type
            val strMap: Map<String, Boolean> = gson.fromJson(json, type)
            strMap.mapKeys { it.key.toInt() }
        } catch (_: Exception) { emptyMap() }
    }

    fun setUserEnabled(context: Context, map: Map<Int, Boolean>) {
        prefs(context).edit()
            .putString(KEY_USER_ENABLED, gson.toJson(map.mapKeys { it.key.toString() }))
            .apply()
    }

    fun getUserColors(context: Context): Map<Int, String> {
        val json = prefs(context).getString(KEY_USER_COLORS, null) ?: return emptyMap()
        return try {
            val type = object : TypeToken<Map<String, String>>() {}.type
            val strMap: Map<String, String> = gson.fromJson(json, type)
            strMap.mapKeys { it.key.toInt() }
                .mapValues { (_, value) -> ColorPalette.migrateStoredColor(value) }
        } catch (_: Exception) { emptyMap() }
    }

    fun setUserColors(context: Context, map: Map<Int, String>) {
        prefs(context).edit()
            .putString(KEY_USER_COLORS, gson.toJson(map.mapKeys { it.key.toString() }))
            .apply()
    }

    fun isUserEnabled(context: Context, userId: Int): Boolean =
        getUserEnabled(context)[userId] ?: true

    fun getUserColor(context: Context, userId: Int): String? =
        getUserColors(context)[userId]

    /** Ensure all users from the list have a default color assigned. */
    fun ensureDefaultColors(context: Context, userIds: List<Int>) {
        val existing = getUserColors(context).toMutableMap()
        var changed = false
        userIds.forEachIndexed { index, id ->
            if (!existing.containsKey(id)) {
                existing[id] = DEFAULT_LABELS[index % DEFAULT_LABELS.size]
                changed = true
            }
        }
        if (changed) setUserColors(context, existing)
    }

    fun isDarkMode(context: Context): Boolean =
        prefs(context).getBoolean(KEY_DARK_MODE, false)

    fun setDarkMode(context: Context, enabled: Boolean) {
        prefs(context).edit().putBoolean(KEY_DARK_MODE, enabled).apply()
    }

    fun getDashboardCacheJson(context: Context): String? =
        prefs(context).getString(KEY_DASHBOARD_CACHE, null)

    fun getDashboardEtag(context: Context): String? =
        prefs(context).getString(KEY_DASHBOARD_ETAG, null)

    fun saveDashboardCache(context: Context, json: String, etag: String?) {
        prefs(context).edit()
            .putString(KEY_DASHBOARD_CACHE, json)
            .putString(KEY_DASHBOARD_ETAG, etag)
            .apply()
    }

    fun clearDashboardCache(context: Context) {
        prefs(context).edit()
            .remove(KEY_DASHBOARD_CACHE)
            .remove(KEY_DASHBOARD_ETAG)
            .apply()
    }

    private const val KEY_DASHBOARD_CACHE = "dashboard_cache"
    private const val KEY_DASHBOARD_ETAG = "dashboard_etag"
    private const val KEY_DEVICE_ID = "device_id"
    private const val KEY_CONNECTION_CONFIGURED = "connection_configured"
    private const val KEY_INSTALLED_UPGRADE_VERSION = "installed_upgrade_version"
    private const val KEY_PENDING_UPGRADE_VERSION = "pending_upgrade_version"
    private const val KEY_INSTALL_FAILURE_MESSAGE = "install_failure_message"

    private fun prefs(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun isConnectionConfigured(context: Context): Boolean {
        ensureConnectionConfiguredFromExisting(context)
        return prefs(context).getBoolean(KEY_CONNECTION_CONFIGURED, false)
    }

    fun setConnectionConfigured(context: Context, configured: Boolean) {
        prefs(context).edit().putBoolean(KEY_CONNECTION_CONFIGURED, configured).apply()
    }

    /** Existing installs that already logged in before this flag existed. */
    private fun ensureConnectionConfiguredFromExisting(context: Context) {
        if (prefs(context).getBoolean(KEY_CONNECTION_CONFIGURED, false)) return
        if (!getAuthToken(context).isNullOrBlank()) {
            setConnectionConfigured(context, true)
        }
    }

    fun getInstalledUpgradeVersion(context: Context): Int =
        prefs(context).getInt(KEY_INSTALLED_UPGRADE_VERSION, 0)

    fun setInstalledUpgradeVersion(context: Context, version: Int) {
        prefs(context).edit().putInt(KEY_INSTALLED_UPGRADE_VERSION, version).apply()
    }

    fun getPendingUpgradeVersion(context: Context): Int =
        prefs(context).getInt(KEY_PENDING_UPGRADE_VERSION, 0)

    fun setPendingUpgradeVersion(context: Context, version: Int) {
        prefs(context).edit().putInt(KEY_PENDING_UPGRADE_VERSION, version).apply()
    }

    fun clearPendingUpgradeVersion(context: Context) {
        prefs(context).edit().remove(KEY_PENDING_UPGRADE_VERSION).apply()
    }

    fun setInstallFailureMessage(context: Context, message: String) {
        prefs(context).edit().putString(KEY_INSTALL_FAILURE_MESSAGE, message).apply()
    }

    fun getInstallFailureMessage(context: Context): String? =
        prefs(context).getString(KEY_INSTALL_FAILURE_MESSAGE, null)?.takeIf { it.isNotBlank() }

    fun clearInstallFailureMessage(context: Context) {
        prefs(context).edit().remove(KEY_INSTALL_FAILURE_MESSAGE).apply()
    }

    /** Promote pending version after a successful APK install (survives app update). */
    fun commitPendingUpgradeVersion(context: Context) {
        val pending = getPendingUpgradeVersion(context)
        if (pending > 0) {
            setInstalledUpgradeVersion(context, pending)
            clearPendingUpgradeVersion(context)
        }
    }
}
