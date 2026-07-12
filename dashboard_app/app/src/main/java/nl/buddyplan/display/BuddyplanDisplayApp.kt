package nl.buddyplan.display

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate

class BuddyplanDisplayApp : Application() {
    override fun onCreate() {
        super.onCreate()
        UpgradeInstallState.reconcile(this)
        AppPreferences.commitPendingUpgradeVersion(this)
        applyDarkMode(this)
    }

    companion object {
        fun applyDarkMode(app: android.content.Context) {
            val mode = if (AppPreferences.isDarkMode(app))
                AppCompatDelegate.MODE_NIGHT_YES
            else
                AppCompatDelegate.MODE_NIGHT_NO
            AppCompatDelegate.setDefaultNightMode(mode)
        }
    }
}
