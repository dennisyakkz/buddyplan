package nl.buddyplan.display.ui

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
                val personLabel = item.person_id?.let { userColors[it] }?.let {
                    ColorPalette.migrateStoredColor(it)
                }
                if (personLabel != null) {
                    val colors = ColorPalette.chipColors(itemView.context, personLabel)
                    val drawable = ColorPalette.chipDrawable(itemView.context, personLabel, 12f)
                    if (colors != null && drawable != null) {
                        val borderColor = ContextCompat.getColor(itemView.context, R.color.tile_border)
                        drawable.setStroke(
                            (2 * itemView.context.resources.displayMetrics.density).toInt(),
                            borderColor,
                        )
                        container.background = drawable
                        title.setTextColor(colors.second)
                        description.setTextColor(colors.second)
                        icon.setTextColor(colors.second)
                    } else {
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
    }
}
