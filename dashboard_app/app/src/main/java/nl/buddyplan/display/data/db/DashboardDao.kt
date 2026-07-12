package nl.buddyplan.display.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction

@Dao
interface DashboardDao {

    @Query("SELECT * FROM cached_tasks")
    suspend fun getAllTasks(): List<CachedTaskEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertTasks(tasks: List<CachedTaskEntity>)

    @Query("DELETE FROM cached_tasks WHERE date >= :start AND date <= :end")
    suspend fun deleteTasksInRange(start: String, end: String)

    @Query("SELECT * FROM week_calendar WHERE weekStart = :weekStart LIMIT 1")
    suspend fun getWeek(weekStart: String): WeekCalendarEntity?

    @Query("SELECT weekStart FROM week_calendar")
    suspend fun getAllWeekStarts(): List<String>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertWeek(week: WeekCalendarEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertWeeks(weeks: List<WeekCalendarEntity>)

    @Query("DELETE FROM week_calendar")
    suspend fun clearWeeks()

    @Query("DELETE FROM cached_tasks")
    suspend fun clearTasks()

    @Query("SELECT * FROM cache_meta WHERE id = 1 LIMIT 1")
    suspend fun getMeta(): CacheMetaEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertMeta(meta: CacheMetaEntity)

    @Transaction
    suspend fun replaceAll(
        tasks: List<CachedTaskEntity>,
        weeks: List<WeekCalendarEntity>,
        meta: CacheMetaEntity,
    ) {
        clearTasks()
        clearWeeks()
        if (tasks.isNotEmpty()) upsertTasks(tasks)
        if (weeks.isNotEmpty()) upsertWeeks(weeks)
        upsertMeta(meta)
    }
}
