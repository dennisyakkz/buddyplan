package nl.buddyplan.display

import android.app.Activity
import android.app.PendingIntent
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import nl.buddyplan.display.data.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.util.concurrent.TimeUnit

object DashboardUpgradeManager {

    data class UpgradeInfo(
        val version: Int,
        val uploadedAt: String?,
    )

    sealed class InstallResult {
        data object Started : InstallResult()
        data class Failed(val message: String) : InstallResult()
    }

    suspend fun fetchServerUpgrade(context: Context): UpgradeInfo? = withContext(Dispatchers.IO) {
        try {
            val response = ApiClient.getApi(context).getDashboardUpgrade()
            UpgradeInfo(response.version, response.uploaded_at)
        } catch (_: Exception) {
            null
        }
    }

    fun isUpdateAvailable(context: Context, serverVersion: Int): Boolean =
        serverVersion > 0 && serverVersion > AppPreferences.getInstalledUpgradeVersion(context)

    fun canInstallPackages(context: Context): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            return context.packageManager.canRequestPackageInstalls()
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            return try {
                @Suppress("DEPRECATION")
                Settings.Secure.getInt(
                    context.contentResolver,
                    Settings.Secure.INSTALL_NON_MARKET_APPS,
                    0,
                ) == 1
            } catch (_: Exception) {
                true
            }
        }
        return true
    }

    /** Opens the system screen where the user can allow APK installs for this app. */
    fun openInstallPermissionSettings(activity: Activity): Boolean {
        val candidates = buildInstallPermissionIntents(activity)
        for (intent in candidates) {
            if (intent.resolveActivity(activity.packageManager) == null) continue
            try {
                activity.startActivity(intent)
                return true
            } catch (_: ActivityNotFoundException) {
                // try next fallback
            }
        }
        return false
    }

    private fun buildInstallPermissionIntents(activity: Activity): List<Intent> {
        val pkg = activity.packageName
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            return listOf(
                Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                    data = Uri.parse("package:$pkg")
                },
                Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES),
                Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                    data = Uri.fromParts("package", pkg, null)
                },
            )
        }
        return listOf(
            Intent(Settings.ACTION_SECURITY_SETTINGS),
            Intent(Settings.ACTION_SETTINGS),
            Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", pkg, null)
            },
        )
    }

    suspend fun downloadApk(context: Context): File? = withContext(Dispatchers.IO) {
        val token = AppPreferences.getAuthToken(context) ?: return@withContext null
        val url = AppPreferences.getServerUrl(context).trimEnd('/') + "/api/app/dashboard-upgrade/download"
        val request = Request.Builder()
            .url(url)
            .header("Authorization", "Bearer $token")
            .build()

        val client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(5, TimeUnit.MINUTES)
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) return@withContext null
            val body = response.body ?: return@withContext null
            val file = File(context.cacheDir, "buddyplan-dashboard-update.apk")
            file.outputStream().use { out ->
                body.byteStream().use { input -> input.copyTo(out) }
            }
            file
        }
    }

    fun installApk(activity: Activity, apkFile: File, serverVersion: Int): InstallResult {
        if (installWithPackageInstaller(activity, apkFile, serverVersion)) {
            return InstallResult.Started
        }
        return installWithIntent(activity, apkFile, serverVersion)
    }

    private fun installWithPackageInstaller(
        activity: Activity,
        apkFile: File,
        serverVersion: Int,
    ): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return false
        return try {
            val packageInstaller = activity.packageManager.packageInstaller
            val params = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL)
            val sessionId = packageInstaller.createSession(params)
            val session = packageInstaller.openSession(sessionId)
            apkFile.inputStream().use { input ->
                session.openWrite("package", 0, apkFile.length()).use { output ->
                    input.copyTo(output)
                    session.fsync(output)
                }
            }
            val callbackIntent = Intent(activity, InstallConfirmActivity::class.java)
            val pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT or
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) PendingIntent.FLAG_MUTABLE else 0
            val pendingIntent = PendingIntent.getActivity(
                activity,
                sessionId,
                callbackIntent,
                pendingFlags,
            )
            AppPreferences.setPendingUpgradeVersion(activity, serverVersion)
            session.commit(pendingIntent.intentSender)
            session.close()
            UpgradeInstallState.markAwaitingConfirm(activity)
            true
        } catch (_: Exception) {
            UpgradeInstallState.clear(activity)
            false
        }
    }

    private fun installWithIntent(
        activity: Activity,
        apkFile: File,
        serverVersion: Int,
    ): InstallResult {
        val uri = FileProvider.getUriForFile(
            activity,
            "${activity.packageName}.fileprovider",
            apkFile,
        )
        val intents = buildList {
            add(Intent(Intent.ACTION_VIEW))
            @Suppress("DEPRECATION")
            add(Intent(Intent.ACTION_INSTALL_PACKAGE))
        }.map { intent ->
            intent.setDataAndType(uri, "application/vnd.android.package-archive")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent
        }

        for (intent in intents) {
            if (intent.resolveActivity(activity.packageManager) == null) continue
            return try {
                AppPreferences.setPendingUpgradeVersion(activity, serverVersion)
                UpgradeInstallState.markAwaitingConfirm(activity)
                activity.startActivity(intent)
                InstallResult.Started
            } catch (_: ActivityNotFoundException) {
                AppPreferences.clearPendingUpgradeVersion(activity)
                continue
            }
        }

        AppPreferences.clearPendingUpgradeVersion(activity)
        return InstallResult.Failed("Geen app gevonden om de update te installeren.")
    }
}
