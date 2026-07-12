package nl.buddyplan.display

import android.content.Context
import android.content.Intent
import android.view.View
import android.widget.Button
import android.widget.FrameLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

object UpgradeInstallFailureUi {

    fun setup(activity: AppCompatActivity) {
        activity.findViewById<Button>(R.id.btnInstallFailureClose)?.setOnClickListener {
            dismiss(activity)
        }
    }

    fun showIfPending(activity: AppCompatActivity) {
        val message = AppPreferences.getInstallFailureMessage(activity) ?: return
        val overlay = activity.findViewById<FrameLayout>(R.id.installFailureOverlay) ?: return
        activity.findViewById<FrameLayout>(R.id.installOverlay)?.visibility = View.GONE
        activity.findViewById<FrameLayout>(R.id.updateOverlay)?.visibility = View.GONE
        activity.findViewById<TextView>(R.id.installFailureMessage)?.text = message
        overlay.visibility = View.VISIBLE
    }

    fun dismiss(activity: AppCompatActivity) {
        AppPreferences.clearInstallFailureMessage(activity)
        activity.findViewById<FrameLayout>(R.id.installFailureOverlay)?.visibility = View.GONE
    }

    fun report(context: Context, message: String) {
        val appContext = context.applicationContext
        UpgradeInstallState.clear(appContext)
        AppPreferences.clearPendingUpgradeVersion(appContext)
        AppPreferences.setInstallFailureMessage(appContext, message)

        val launch = Intent(appContext, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }
        appContext.startActivity(launch)
    }
}
