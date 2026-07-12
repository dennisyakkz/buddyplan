package nl.buddyplan.display.ui

import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Paint
import android.graphics.drawable.GradientDrawable
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import nl.buddyplan.display.FaIconHelper
import nl.buddyplan.display.R
import nl.buddyplan.display.data.TodoItem

class TodoAdapter(
    private val onItemClick: (TodoItem) -> Unit
) : RecyclerView.Adapter<TodoAdapter.TodoViewHolder>() {

    private val items = mutableListOf<TodoItem>()
    private var userColors: Map<Int, String> = emptyMap()
    private var userEnabled: Map<Int, Boolean> = emptyMap()
    private var allItems: List<TodoItem> = emptyList()

    fun submitList(todos: List<TodoItem>) {
        allItems = todos
        applyFilters()
    }

    fun updateUserSettings(colors: Map<Int, String>, enabled: Map<Int, Boolean>) {
        userColors = colors
        userEnabled = enabled
        applyFilters()
    }

    private fun applyFilters() {
        items.clear()
        items.addAll(allItems.filter { item ->
            val pid = item.person_id
            if (pid != null) userEnabled[pid] ?: true else true
        })
        notifyDataSetChanged()
    }

    fun markCompleted(id: String) {
        val index = items.indexOfFirst { it.id == id }
        if (index < 0) return
        items[index].completed = true
        notifyItemChanged(index)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TodoViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_todo, parent, false)
        return TodoViewHolder(view)
    }

    override fun onBindViewHolder(holder: TodoViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    inner class TodoViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val container: LinearLayout = itemView.findViewById(R.id.tileContainer)
        private val icon: TextView = itemView.findViewById(R.id.tileIcon)
        private val title: TextView = itemView.findViewById(R.id.tileTitle)
        private val description: TextView = itemView.findViewById(R.id.tileDescription)
        private val thumb: ImageView = itemView.findViewById(R.id.tileThumb)

        fun bind(item: TodoItem) {
            FaIconHelper.applyIcon(icon, item.icon)
            title.text = item.title
            description.text = item.description

            if (item.completed) {
                container.setBackgroundResource(R.drawable.tile_background_completed)
                title.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_completed))
                description.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_completed))
                title.paintFlags = title.paintFlags or Paint.STRIKE_THRU_TEXT_FLAG
                thumb.visibility = View.VISIBLE
                itemView.alpha = 0.75f
                itemView.isEnabled = false
                icon.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_completed))
            } else {
                val personColor = item.person_id?.let { userColors[it] }
                if (personColor != null) {
                    try {
                        val rawColor = Color.parseColor(personColor)
                        val bgColor = adaptColorForNightMode(rawColor, itemView.context)
                        val drawable = GradientDrawable().apply {
                            shape = GradientDrawable.RECTANGLE
                            cornerRadius = (8 * itemView.context.resources.displayMetrics.density)
                            setColor(bgColor)
                        }
                        container.background = drawable
                        val textColor = contrastColor(bgColor)
                        title.setTextColor(textColor)
                        description.setTextColor(textColor)
                        icon.setTextColor(textColor)
                    } catch (_: IllegalArgumentException) {
                        applyDefaultStyle()
                    }
                } else {
                    applyDefaultStyle()
                }
                title.paintFlags = title.paintFlags and Paint.STRIKE_THRU_TEXT_FLAG.inv()
                thumb.visibility = View.GONE
                itemView.alpha = 1f
                itemView.isEnabled = true
                itemView.setOnClickListener { onItemClick(item) }
            }
        }

        private fun applyDefaultStyle() {
            container.setBackgroundResource(R.drawable.tile_background)
            title.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_primary))
            description.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_secondary))
            icon.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_primary))
        }

        private fun contrastColor(bgColor: Int): Int {
            val r = Color.red(bgColor) / 255.0
            val g = Color.green(bgColor) / 255.0
            val b = Color.blue(bgColor) / 255.0
            val luminance = 0.299 * r + 0.587 * g + 0.114 * b
            return if (luminance > 0.5) Color.BLACK else Color.WHITE
        }

        /**
         * In dark mode: reduce brightness and slightly desaturate so the user's chosen
         * accent colours remain recognisable but don't overpower a dark background.
         */
        private fun adaptColorForNightMode(color: Int, context: android.content.Context): Int {
            val nightMode = context.resources.configuration.uiMode and
                    Configuration.UI_MODE_NIGHT_MASK
            if (nightMode != Configuration.UI_MODE_NIGHT_YES) return color

            val hsv = FloatArray(3)
            Color.colorToHSV(color, hsv)
            hsv[1] = (hsv[1] * 0.85f).coerceIn(0f, 1f) // slightly desaturate
            hsv[2] = (hsv[2] * 0.45f).coerceIn(0f, 1f) // significantly darker
            return Color.HSVToColor(hsv)
        }
    }
}
