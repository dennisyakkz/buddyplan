package nl.buddyplan.display.ui

import android.content.Context
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.ViewConfiguration
import android.widget.FrameLayout
import kotlin.math.abs

/**
 * Intercepts horizontal swipes over child views.
 * Swipe left → previous, swipe right → next.
 */
class SwipeNavLayout @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : FrameLayout(context, attrs) {

    var onSwipeToPrevious: (() -> Unit)? = null
    var onSwipeToNext: (() -> Unit)? = null

    private var downX = 0f
    private var downY = 0f
    private var tracking = false
    private val touchSlop = ViewConfiguration.get(context).scaledTouchSlop

    override fun onInterceptTouchEvent(ev: MotionEvent): Boolean {
        when (ev.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                downX = ev.x
                downY = ev.y
                tracking = true
                return false
            }
            MotionEvent.ACTION_MOVE -> {
                if (!tracking) return false
                val diffX = ev.x - downX
                val diffY = ev.y - downY
                if (abs(diffX) > touchSlop && abs(diffX) > abs(diffY)) {
                    return true
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                tracking = false
            }
        }
        return false
    }

    override fun onTouchEvent(ev: MotionEvent): Boolean {
        when (ev.actionMasked) {
            MotionEvent.ACTION_UP -> {
                val diffX = ev.x - downX
                val diffY = ev.y - downY
                tracking = false
                if (abs(diffX) > abs(diffY) && abs(diffX) >= SWIPE_MIN_PX) {
                    if (diffX < 0) {
                        onSwipeToPrevious?.invoke()
                    } else {
                        onSwipeToNext?.invoke()
                    }
                    return true
                }
            }
            MotionEvent.ACTION_CANCEL -> tracking = false
        }
        return true
    }

    companion object {
        private const val SWIPE_MIN_PX = 72f
    }
}
