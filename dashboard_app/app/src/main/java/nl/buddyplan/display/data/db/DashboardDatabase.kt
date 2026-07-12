package nl.buddyplan.display.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [CachedTaskEntity::class, WeekCalendarEntity::class, CacheMetaEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class DashboardDatabase : RoomDatabase() {
    abstract fun dashboardDao(): DashboardDao

    companion object {
        @Volatile
        private var instance: DashboardDatabase? = null

        fun getInstance(context: Context): DashboardDatabase {
            return instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    DashboardDatabase::class.java,
                    "buddyplan_dashboard_cache",
                ).build().also { instance = it }
            }
        }
    }
}
