package nl.buddyplan.display.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import nl.buddyplan.display.R
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

class AnalogClockView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    var time: String? = null
        set(value) {
            field = value
            invalidate()
        }

    private val faceFillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }
    private val faceStrokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
    }
    private val tickPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val numberPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textAlign = Paint.Align.CENTER
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
    }
    private val handPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
    }
    private val centerPaint = Paint(Paint.ANTI_ALIAS_FLAG)

    override fun onDraw(canvas: Canvas) {
        val size = min(width, height).toFloat()
        val cx = width / 2f
        val cy = height / 2f
        val radius = size / 2f - dp(4f)

        val primary = ContextCompat.getColor(context, R.color.text_primary)
        val secondary = ContextCompat.getColor(context, R.color.text_secondary)
        val faceFill = ContextCompat.getColor(context, R.color.calendar_cell_bg)

        faceFillPaint.color = faceFill
        faceStrokePaint.color = secondary
        faceStrokePaint.strokeWidth = dp(2f)
        tickPaint.color = primary
        tickPaint.strokeWidth = dp(2f)
        numberPaint.color = primary
        numberPaint.textSize = radius * 0.28f
        handPaint.color = primary
        centerPaint.color = primary

        canvas.drawCircle(cx, cy, radius, faceFillPaint)
        canvas.drawCircle(cx, cy, radius, faceStrokePaint)
        drawHourMarkers(canvas, cx, cy, radius)

        val parsed = parseTime(time) ?: return
        val (hour, minute) = parsed
        drawHands(canvas, cx, cy, radius, hour, minute)
        canvas.drawCircle(cx, cy, dp(3f), centerPaint)
    }

    private fun drawHourMarkers(canvas: Canvas, cx: Float, cy: Float, radius: Float) {
        for (hour in 1..12) {
            val angle = Math.toRadians(hour * 30.0 - 90.0)
            val cosA = cos(angle).toFloat()
            val sinA = sin(angle).toFloat()

            val tickOuter = radius * 0.94f
            val tickInner = radius * 0.82f
            canvas.drawLine(
                cx + cosA * tickInner,
                cy + sinA * tickInner,
                cx + cosA * tickOuter,
                cy + sinA * tickOuter,
                tickPaint,
            )

            val numberRadius = radius * 0.62f
            val nx = cx + cosA * numberRadius
            val ny = cy + sinA * numberRadius
            val textY = ny - (numberPaint.descent() + numberPaint.ascent()) / 2f
            canvas.drawText(hour.toString(), nx, textY, numberPaint)
        }
    }

    private fun drawHands(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        radius: Float,
        hour: Int,
        minute: Int,
    ) {
        val hourAngle = Math.toRadians((hour % 12) * 30.0 + minute * 0.5 - 90.0)
        val minuteAngle = Math.toRadians(minute * 6.0 - 90.0)

        handPaint.strokeWidth = dp(4f)
        val hourLen = radius * 0.38f
        canvas.drawLine(
            cx,
            cy,
            cx + (cos(hourAngle) * hourLen).toFloat(),
            cy + (sin(hourAngle) * hourLen).toFloat(),
            handPaint,
        )

        handPaint.strokeWidth = dp(2.5f)
        val minuteLen = radius * 0.56f
        canvas.drawLine(
            cx,
            cy,
            cx + (cos(minuteAngle) * minuteLen).toFloat(),
            cy + (sin(minuteAngle) * minuteLen).toFloat(),
            handPaint,
        )
    }

    private fun parseTime(value: String?): Pair<Int, Int>? {
        if (value.isNullOrBlank()) return null
        val parts = value.trim().split(":")
        if (parts.size != 2) return null
        return try {
            val hour = parts[0].toInt()
            val minute = parts[1].toInt()
            if (hour !in 0..23 || minute !in 0..59) null else hour to minute
        } catch (_: NumberFormatException) {
            null
        }
    }

    private fun dp(value: Float): Float =
        value * resources.displayMetrics.density

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val size = dp(96f).toInt()
        setMeasuredDimension(size, size)
    }
}
