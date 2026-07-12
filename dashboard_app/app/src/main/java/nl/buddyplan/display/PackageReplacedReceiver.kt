package nl.buddyplan.display

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Restarts the dashboard after a successful in-place APK update.
 */
class PackageReplacedReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_MY_PACKAGE_REPLACED) return

        val appContext = context.applicationContext
        AppPreferences.commitPendingUpgradeVersion(appContext)
        UpgradeInstallState.clear(appContext)

        val launch = Intent(appContext, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        appContext.startActivity(launch)
    }
}
