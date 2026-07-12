package nl.buddyplan.display

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageInstaller
import android.os.Build

class InstallStatusReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
        when (status) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val confirmIntent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    intent.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra(Intent.EXTRA_INTENT)
                }
                if (confirmIntent != null) {
                    confirmIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    try {
                        UpgradeInstallState.markInstalling(context)
                        context.startActivity(confirmIntent)
                    } catch (_: Exception) {
                        UpgradeInstallFailureUi.report(
                            context,
                            context.getString(R.string.update_install_start_failed),
                        )
                    }
                } else {
                    UpgradeInstallFailureUi.report(
                        context,
                        context.getString(R.string.update_install_confirm_missing),
                    )
                }
            }
            PackageInstaller.STATUS_SUCCESS -> {
                UpgradeInstallState.clear(context)
            }
            else -> {
                val message = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)
                UpgradeInstallFailureUi.report(
                    context,
                    message ?: context.getString(R.string.update_install_failed),
                )
            }
        }
    }
}
