package nl.buddyplan.display

import android.content.Context
import android.content.Intent
import android.view.View
import android.widget.Button
import android.widget.FrameLayout
import androidx.appcompat.app.AppCompatActivity

object SessionExpiredUi {

    fun setup(activity: AppCompatActivity, onNavigateToLogin: () -> Unit) {
        activity.findViewById<Button>(R.id.btnSessionExpiredClose)?.setOnClickListener {
            dismiss(activity)
            onNavigateToLogin()
        }
    }

    fun show(activity: AppCompatActivity) {
        val overlay = activity.findViewById<FrameLayout>(R.id.sessionExpiredOverlay) ?: return
        overlay.visibility = View.VISIBLE
    }

    fun dismiss(activity: AppCompatActivity) {
        activity.findViewById<FrameLayout>(R.id.sessionExpiredOverlay)?.visibility = View.GONE
    }

    fun clearSession(context: Context) {
        val appContext = context.applicationContext
        AppPreferences.setAuthToken(appContext, null)
    }

    fun openLoginSettings(activity: AppCompatActivity) {
        val intent = Intent(activity, SettingsActivity::class.java).apply {
            putExtra(SettingsActivity.EXTRA_INITIAL_TAB, SettingsActivity.TAB_CONNECTIE)
        }
        activity.startActivity(intent)
    }

    fun navigateToLogin(activity: AppCompatActivity) {
        if (AppPreferences.isPinEnabled(activity)) {
            val pin = AppPreferences.getPinCode(activity)
            PinEntryDialog(activity, pin, onSuccess = { openLoginSettings(activity) }).show()
        } else {
            openLoginSettings(activity)
        }
    }
}
