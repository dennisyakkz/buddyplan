package nl.buddyplan.display

import android.content.Intent
import android.content.pm.PackageInstaller
import android.os.Build
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

/**
 * Handles PackageInstaller session callbacks and launches the system confirm UI when needed.
 */
class InstallConfirmActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)
        val message = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)

        when (status) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val confirmIntent = readConfirmIntent(intent)
                if (confirmIntent != null) {
                    try {
                        UpgradeInstallState.markInstalling(this)
                        startActivity(confirmIntent)
                    } catch (_: Exception) {
                        UpgradeInstallFailureUi.report(
                            this,
                            getString(R.string.update_install_start_failed),
                        )
                    }
                } else {
                    UpgradeInstallFailureUi.report(
                        this,
                        getString(R.string.update_install_confirm_missing),
                    )
                }
            }
            PackageInstaller.STATUS_SUCCESS -> {
                UpgradeInstallState.clear(this)
            }
            else -> {
                UpgradeInstallFailureUi.report(
                    this,
                    message ?: getString(R.string.update_install_failed),
                )
            }
        }
        finish()
    }

    private fun readConfirmIntent(intent: Intent): Intent? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(Intent.EXTRA_INTENT)
        }
    }
}
