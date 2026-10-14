package nl.buddyplan.display

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import java.util.Locale

data class BatterySnapshot(
    val levelPercent: String,
    val status: String,
    val usbConnected: String,
    val acConnected: String,
    val wirelessConnected: String,
    val currentAvg: String,
    val currentNow: String,
    val voltage: String,
    val temperature: String,
    val health: String,
    val chargeCounter: String,
    val energyCounter: String,
)

object BatteryInfoReader {

    fun read(context: Context): BatterySnapshot {
        @Suppress("UnspecifiedRegisterReceiverFlag")
        val intent = context.registerReceiver(
            null,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED),
        )
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager

        return BatterySnapshot(
            levelPercent = formatCapacity(bm, intent),
            status = formatStatus(bm, intent),
            usbConnected = formatPlugged(intent, BatteryManager.BATTERY_PLUGGED_USB, "usb"),
            acConnected = formatPlugged(intent, BatteryManager.BATTERY_PLUGGED_AC, "ac"),
            wirelessConnected = formatPlugged(intent, BatteryManager.BATTERY_PLUGGED_WIRELESS, "wireless"),
            currentAvg = formatCurrentUa(
                bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_AVERAGE),
            ),
            currentNow = formatCurrentUa(
                bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW),
            ),
            voltage = formatVoltage(intent),
            temperature = formatTemperature(intent),
            health = formatHealth(intent),
            chargeCounter = formatChargeCounter(
                bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER),
            ),
            energyCounter = formatEnergyCounter(bm),
        )
    }

    /** Prefer [BatteryManager.BATTERY_PROPERTY_CAPACITY], else EXTRA_LEVEL/EXTRA_SCALE. */
    private fun formatCapacity(bm: BatteryManager, intent: Intent?): String {
        val fromProperty = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        if (fromProperty in 0..100) return "$fromProperty%"

        val level = intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale = intent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        if (level >= 0 && scale > 0) return "${(level * 100) / scale}%"
        return "—"
    }

    /** Prefer BATTERY_PROPERTY_STATUS (API 26+), else EXTRA_STATUS. */
    private fun formatStatus(bm: BatteryManager, intent: Intent?): String {
        val statusCode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val fromProperty = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_STATUS)
            if (fromProperty != Int.MIN_VALUE) fromProperty
            else intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        } else {
            intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        }
        return when (statusCode) {
            BatteryManager.BATTERY_STATUS_CHARGING -> "Charging"
            BatteryManager.BATTERY_STATUS_DISCHARGING -> "Discharging"
            BatteryManager.BATTERY_STATUS_FULL -> "Full"
            BatteryManager.BATTERY_STATUS_NOT_CHARGING -> "Not charging"
            else -> "Unknown"
        }
    }

    /** EXTRA_HEALTH + EXTRA_TECHNOLOGY (no BatteryManager property for health). */
    private fun formatHealth(intent: Intent?): String {
        val healthCode = intent?.getIntExtra(BatteryManager.EXTRA_HEALTH, -1) ?: -1
        val healthName = when (healthCode) {
            BatteryManager.BATTERY_HEALTH_GOOD -> "Good"
            BatteryManager.BATTERY_HEALTH_OVERHEAT -> "Overheat"
            BatteryManager.BATTERY_HEALTH_DEAD -> "Dead"
            BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE -> "Over voltage"
            BatteryManager.BATTERY_HEALTH_UNSPECIFIED_FAILURE -> "Failure"
            BatteryManager.BATTERY_HEALTH_COLD -> "Cold"
            else -> "Unknown"
        }
        val technology = intent
            ?.getStringExtra(BatteryManager.EXTRA_TECHNOLOGY)
            ?.takeIf { it.isNotBlank() }
        return if (technology != null) "$healthName, $technology" else healthName
    }

    /** EXTRA_PLUGGED → BATTERY_PLUGGED_USB / AC / WIRELESS. */
    private fun formatPlugged(intent: Intent?, flag: Int, label: String): String {
        val plugged = intent?.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0) ?: 0
        val online = (plugged and flag) != 0
        return if (online) "Ja ($label/online = 1)" else "Nee ($label/online = 0)"
    }

    /**
     * CURRENT_AVERAGE / CURRENT_NOW via getIntProperty — value in µA.
     * Sign is OEM-dependent; on most devices negative means discharging.
     */
    private fun formatCurrentUa(valueUa: Int): String {
        if (valueUa == Int.MIN_VALUE) return "—"
        return when {
            valueUa < 0 -> "$valueUa µA (negatief = ontladen)"
            valueUa > 0 -> "$valueUa µA (positief = laden)"
            else -> "0 µA"
        }
    }

    /** EXTRA_VOLTAGE in mV. */
    private fun formatVoltage(intent: Intent?): String {
        val voltageMv = intent?.getIntExtra(BatteryManager.EXTRA_VOLTAGE, -1) ?: -1
        if (voltageMv <= 0) return "—"
        return String.format(Locale.GERMANY, "%.3f V", voltageMv / 1000.0)
    }

    /** EXTRA_TEMPERATURE in tenths of a degree Celsius. */
    private fun formatTemperature(intent: Intent?): String {
        val tempTenths = intent?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, Int.MIN_VALUE)
            ?: Int.MIN_VALUE
        if (tempTenths == Int.MIN_VALUE) return "—"
        return String.format(Locale.GERMANY, "%.1f °C", tempTenths / 10.0)
    }

    /** BATTERY_PROPERTY_CHARGE_COUNTER — remaining capacity in µAh. */
    private fun formatChargeCounter(valueUah: Int): String {
        if (valueUah == Int.MIN_VALUE) return "—"
        return "$valueUah µAh"
    }

    /** BATTERY_PROPERTY_ENERGY_COUNTER — remaining energy in nWh (API 21+, often unsupported). */
    private fun formatEnergyCounter(bm: BatteryManager): String {
        val valueNwh = bm.getLongProperty(BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER)
        if (valueNwh == Long.MIN_VALUE) return "—"
        return "$valueNwh nWh"
    }
}
