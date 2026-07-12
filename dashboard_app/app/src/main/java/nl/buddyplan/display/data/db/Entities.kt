package nl.buddyplan.display.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_tasks")
data class CachedTaskEntity(
    @PrimaryKey val id: String,
    val title: String,
    val description: String,
    val icon: String,
    val completed: Boolean,
    val personId: Int?,
    val date: String,
)

@Entity(tableName = "week_calendar")
data class WeekCalendarEntity(
    @PrimaryKey val weekStart: String,
    val weekDaysJson: String,
    val calendarJson: String,
)

@Entity(tableName = "cache_meta")
data class CacheMetaEntity(
    @PrimaryKey val id: Int = 1,
    val etag: String? = null,
    val lastSyncMs: Long = 0L,
)
