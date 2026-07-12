package nl.buddyplan.display

import android.app.Dialog
import android.content.Context
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import android.view.View
import android.view.Window
import android.widget.Button
import android.widget.TextView

class PinEntryDialog(
    context: Context,
    private val expectedPin: String,
    private val onSuccess: () -> Unit,
    private val onCancel: (() -> Unit)? = null,
) : Dialog(context) {

    private var entered = StringBuilder()
    private lateinit var dots: List<View>
    private lateinit var errorText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestWindowFeature(Window.FEATURE_NO_TITLE)
        setContentView(R.layout.dialog_pin_entry)
        window?.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
        setCancelable(false)

        dots = listOf(
            findViewById(R.id.pinDot1),
            findViewById(R.id.pinDot2),
            findViewById(R.id.pinDot3),
            findViewById(R.id.pinDot4),
        )
        errorText = findViewById(R.id.pinError)

        val numButtons = mapOf(
            R.id.pin0 to "0", R.id.pin1 to "1", R.id.pin2 to "2",
            R.id.pin3 to "3", R.id.pin4 to "4", R.id.pin5 to "5",
            R.id.pin6 to "6", R.id.pin7 to "7", R.id.pin8 to "8",
            R.id.pin9 to "9",
        )
        numButtons.forEach { (id, digit) ->
            findViewById<Button>(id).setOnClickListener { pressDigit(digit) }
        }

        findViewById<Button>(R.id.pinBackspace).setOnClickListener { backspace() }
        findViewById<Button>(R.id.pinCancel).setOnClickListener {
            dismiss()
            onCancel?.invoke()
        }

        updateDots()
    }

    private fun pressDigit(digit: String) {
        if (entered.length >= 4) return
        entered.append(digit)
        updateDots()
        errorText.visibility = View.INVISIBLE

        if (entered.length == 4) {
            if (entered.toString() == expectedPin) {
                dismiss()
                onSuccess()
            } else {
                errorText.text = "Onjuiste pincode"
                errorText.visibility = View.VISIBLE
                entered.clear()
                updateDots()
            }
        }
    }

    private fun backspace() {
        if (entered.isNotEmpty()) {
            entered.deleteCharAt(entered.length - 1)
            updateDots()
            errorText.visibility = View.INVISIBLE
        }
    }

    private fun updateDots() {
        dots.forEachIndexed { i, dot ->
            dot.setBackgroundResource(
                if (i < entered.length) R.drawable.pin_dot_filled else R.drawable.pin_dot_empty
            )
        }
    }
}
