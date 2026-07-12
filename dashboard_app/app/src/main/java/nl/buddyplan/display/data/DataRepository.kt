package nl.buddyplan.display.data

import android.content.Context
import android.os.Build
import android.util.Log
import nl.buddyplan.display.AppPreferences
import nl.buddyplan.display.data.api.ApiClient
import nl.buddyplan.display.data.api.BuddyplanApi
import nl.buddyplan.display.data.db.CacheMetaEntity
import nl.buddyplan.display.data.db.CachedTaskEntity
import nl.buddyplan.display.data.db.DashboardDao
import nl.buddyplan.display.data.db.DashboardDatabase
import nl.buddyplan.display.data.db.WeekCalendarEntity
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import retrofit2.HttpException

object DataRepository {

    private const val TAG = "DataRepository"
    private const val MAX_STALE_MS = 2 * 60 * 1000L

    private val gson = Gson()
    private val cacheMutex = Mutex()

    private var cachedEtag: String? = null
    private var cachedBundle: DashboardCacheBundle? = null
    private var lastSuccessfulSyncMs: Long = 0L
    private var dao: DashboardDao? = null
    private var initialized = false

    private sealed class FetchResult<out T> {
        data class Ok<T>(val value: T) : FetchResult<T>()
        object AuthRequired : FetchResult<Nothing>()
        object Failed : FetchResult<Nothing>()
    }

    suspend fun reset(context: Context) = cacheMutex.withLock {
        cachedEtag = null
        cachedBundle = null
        lastSuccessfulSyncMs = 0L
        val dbDao = ensureDao(context)
        dbDao.clearTasks()
        dbDao.clearWeeks()
        dbDao.upsertMeta(CacheMetaEntity())
        AppPreferences.clearDashboardCache(context.applicationContext)
    }

    suspend fun initCache(context: Context) = cacheMutex.withLock {
        if (initialized && cachedBundle != null) return@withLock
        val appContext = context.applicationContext
        ensureDao(appContext)
        migrateFromSharedPreferencesIfNeeded(appContext)
        loadFromRoom()
        initialized = true
    }

    fun getCachedDashboard(viewWeekStart: String? = null): DashboardData? {
        val bundle = cachedBundle ?: return null
        val weekStart = viewWeekStart ?: WeekDates.mondayOfToday()
        return dashboardForWeek(bundle, weekStart)
            ?: bundle.weeks.minByOrNull { (cachedWeekStart, _) ->
                kotlin.math.abs(WeekDates.weeksBetween(cachedWeekStart, weekStart))
            }?.let { (fallbackWeekStart, _) ->
                dashboardForWeek(bundle, fallbackWeekStart)
            }
    }

    suspend fun syncFromNetwork(
        context: Context,
        force: Boolean = false,
        viewWeekStart: String? = null,
    ): SyncResult = withContext(Dispatchers.IO) {
        cacheMutex.withLock {
            val appContext = context.applicationContext
            ensureDao(appContext)
            val weekStart = viewWeekStart ?: WeekDates.mondayOfToday()
            var etagValue: String? = null

            if (!force) {
                val stale = lastSuccessfulSyncMs == 0L ||
                    System.currentTimeMillis() - lastSuccessfulSyncMs > MAX_STALE_MS
                if (!stale) {
                    when (val etag = fetchEtag(appContext)) {
                        is FetchResult.AuthRequired -> return@withLock SyncResult.AuthRequired
                        is FetchResult.Failed -> return@withLock SyncResult.Failed
                        is FetchResult.Ok -> {
                            etagValue = etag.value
                            if (etag.value == cachedEtag && cachedBundle != null) {
                                val data = dashboardForWeek(cachedBundle!!, weekStart)
                                return@withLock if (data != null) {
                                    SyncResult.Unchanged(data)
                                } else {
                                    SyncResult.Failed
                                }
                            }
                        }
                    }
                }
            }

            val weeksToLoad = weeksToRefresh(weekStart)
            when (val refreshed = refreshWeeksAndTasks(appContext, weeksToLoad)) {
                is FetchResult.AuthRequired -> SyncResult.AuthRequired
                is FetchResult.Failed -> SyncResult.Failed
                is FetchResult.Ok -> {
                    cachedBundle = refreshed.value
                    lastSuccessfulSyncMs = System.currentTimeMillis()
                    if (etagValue != null) {
                        cachedEtag = etagValue
                    } else {
                        when (val etag = fetchEtag(appContext)) {
                            is FetchResult.Ok -> cachedEtag = etag.value
                            else -> cachedEtag = null
                        }
                    }
                    persistCache(appContext)
                    val data = dashboardForWeek(refreshed.value, weekStart)
                        ?: return@withLock SyncResult.Failed
                    SyncResult.Success(data)
                }
            }
        }
    }

    suspend fun loadWeek(context: Context, weekStart: String): DashboardData? =
        withContext(Dispatchers.IO) {
            cacheMutex.withLock {
                val appContext = context.applicationContext
                ensureDao(appContext)
                cachedBundle?.let { bundle ->
                    dashboardForWeek(bundle, weekStart)?.let { data ->
                        maybePrefetch(appContext, weekStart)
                        return@withLock data
                    }
                }
                when (fetchWeeksWithTasks(appContext, listOf(weekStart))) {
                    is FetchResult.AuthRequired, FetchResult.Failed -> {
                        getCachedDashboard(weekStart)
                    }
                    is FetchResult.Ok -> {
                        persistCache(appContext)
                        val data = dashboardForWeek(cachedBundle!!, weekStart)
                        maybePrefetch(appContext, weekStart)
                        data
                    }
                }
            }
        }

    suspend fun reportCompletion(context: Context, taskId: String) = withContext(Dispatchers.IO) {
        cacheMutex.withLock {
            val appContext = context.applicationContext
            try {
                val api = ApiClient.getApi(appContext)
                val response = api.completeTask(taskId)
                if (response.code() == 401) return@withLock
                response.errorBody()?.close()
                cachedEtag = null
                cachedBundle = cachedBundle?.let { bundle ->
                    bundle.copy(
                        tasks = bundle.tasks.map { task ->
                            if (task.id == taskId) task.copy(completed = true) else task
                        },
                    )
                }
                persistCache(appContext)
            } catch (e: Exception) {
                Log.w(TAG, "reportCompletion failed", e)
            }
        }
    }

    suspend fun login(context: Context, username: String, password: String): LoginResult? =
        withContext(Dispatchers.IO) {
            try {
                val api = ApiClient.getApi(context)
                val deviceName = "${Build.MANUFACTURER} ${Build.MODEL}".trim()
                val response = api.login(
                    mapOf(
                        "username" to username,
                        "password" to password,
                        "device_id" to AppPreferences.getDeviceId(context),
                        "device_name" to deviceName,
                        "device_type" to "dashboard",
                    ),
                )
                LoginResult(response.token, response.person_id, response.name)
            } catch (e: Exception) {
                Log.w(TAG, "login failed", e)
                null
            }
        }

    suspend fun fetchAppUsers(context: Context): List<Pair<Int, String>>? =
        withContext(Dispatchers.IO) {
            try {
                val api = ApiClient.getApi(context)
                api.getAppUsers().map { Pair(it.id, it.name) }
            } catch (e: Exception) {
                Log.w(TAG, "fetchAppUsers failed", e)
                null
            }
        }

    // -------------------------------------------------------------------------
    // Room persistence
    // -------------------------------------------------------------------------

    private fun ensureDao(context: Context): DashboardDao {
        if (dao == null) {
            dao = DashboardDatabase.getInstance(context).dashboardDao()
        }
        return dao!!
    }

    private suspend fun loadFromRoom() {
        val dbDao = dao ?: return
        val tasks = dbDao.getAllTasks().map { it.toCachedTaskItem() }
        val weekStarts = dbDao.getAllWeekStarts()
        val weeks = mutableMapOf<String, WeekCalendarData>()
        for (weekStart in weekStarts) {
            val entity = dbDao.getWeek(weekStart) ?: continue
            weeks[weekStart] = entity.toWeekCalendarData()
        }
        cachedBundle = DashboardCacheBundle(tasks = tasks, weeks = weeks)
        val meta = dbDao.getMeta()
        cachedEtag = meta?.etag
        lastSuccessfulSyncMs = meta?.lastSyncMs ?: 0L
    }

    private suspend fun persistCache(context: Context) {
        val bundle = cachedBundle ?: return
        val dbDao = ensureDao(context)
        dbDao.upsertTasks(bundle.tasks.map { it.toEntity() })
        dbDao.upsertWeeks(bundle.weeks.map { (weekStart, data) ->
            WeekCalendarEntity(
                weekStart = weekStart,
                weekDaysJson = gson.toJson(data.weekDays),
                calendarJson = gson.toJson(data.calendar),
            )
        })
        dbDao.upsertMeta(
            CacheMetaEntity(
                etag = cachedEtag,
                lastSyncMs = lastSuccessfulSyncMs,
            ),
        )
        AppPreferences.saveDashboardCache(context, gson.toJson(bundle), cachedEtag)
    }

    private suspend fun migrateFromSharedPreferencesIfNeeded(context: Context) {
        val json = AppPreferences.getDashboardCacheJson(context) ?: return
        try {
            val bundle = try {
                gson.fromJson(json, DashboardCacheBundle::class.java)
            } catch (_: Exception) {
                val legacy = gson.fromJson(json, DashboardData::class.java)
                val weekStart = WeekDates.mondayOfToday()
                DashboardCacheBundle(
                    tasks = legacy.todo.map { todo ->
                        CachedTaskItem(
                            id = todo.id,
                            title = todo.title,
                            description = todo.description,
                            icon = todo.icon,
                            completed = todo.completed,
                            person_id = todo.person_id,
                            date = WeekDates.todayIso(),
                        )
                    },
                    weeks = mapOf(
                        weekStart to WeekCalendarData(
                            weekDays = legacy.weekDays,
                            calendar = legacy.calendar,
                        ),
                    ),
                )
            }
            cachedBundle = bundle
            cachedEtag = AppPreferences.getDashboardEtag(context)
            persistCache(context)
        } catch (e: Exception) {
            Log.w(TAG, "SharedPreferences cache migration failed", e)
        }
    }

    // -------------------------------------------------------------------------
    // Cache helpers
    // -------------------------------------------------------------------------

    private fun weeksToRefresh(viewWeekStart: String): List<String> {
        val weeks = WeekDates.defaultWindowWeekStarts().toMutableSet()
        cachedBundle?.weeks?.keys?.forEach { weeks.add(it) }
        weeks.add(viewWeekStart)
        return weeks.sorted()
    }

    private fun dashboardForWeek(bundle: DashboardCacheBundle, weekStart: String): DashboardData? {
        val week = bundle.weeks[weekStart] ?: return null
        val today = WeekDates.todayIso()
        val todos = bundle.tasks
            .filter { it.date == today }
            .map { it.toTodoItem() }
        return DashboardData(
            todo = todos,
            weekDays = week.weekDays,
            calendar = week.calendar,
        )
    }

    private fun CachedTaskItem.toTodoItem() = TodoItem(
        id = id,
        title = title,
        description = description,
        icon = icon,
        completed = completed,
        person_id = person_id,
    )

    private suspend fun maybePrefetch(context: Context, currentWeekStart: String) {
        val bundle = cachedBundle ?: return
        if (bundle.weeks.isEmpty()) return

        val sortedWeeks = bundle.weeks.keys.sorted()
        val minWeek = sortedWeeks.first()
        val maxWeek = sortedWeeks.last()

        val toFetch = mutableListOf<String>()

        if (WeekDates.weeksBetween(currentWeekStart, maxWeek) <= WeekDates.PREFETCH_THRESHOLD_WEEKS) {
            val start = WeekDates.addWeeks(maxWeek, 1)
            for (i in 0 until WeekDates.PREFETCH_CHUNK_WEEKS) {
                toFetch.add(WeekDates.addWeeks(start, i))
            }
        }

        if (WeekDates.weeksBetween(minWeek, currentWeekStart) <= WeekDates.PREFETCH_THRESHOLD_WEEKS) {
            val end = WeekDates.addWeeks(minWeek, -1)
            for (i in WeekDates.PREFETCH_CHUNK_WEEKS - 1 downTo 0) {
                toFetch.add(WeekDates.addWeeks(end, -i))
            }
        }

        val missing = toFetch.filter { !bundle.weeks.containsKey(it) }
        if (missing.isEmpty()) return

        fetchWeeksWithTasks(context, missing)
        persistCache(context)
    }

    private suspend fun fetchWeeksWithTasks(
        context: Context,
        weekStarts: List<String>,
    ): FetchResult<Unit> {
        when (fetchAndMergeWeeks(context, weekStarts, mergeIntoExisting = true)) {
            is FetchResult.AuthRequired -> return FetchResult.AuthRequired
            is FetchResult.Failed -> if (cachedBundle == null) return FetchResult.Failed
            is FetchResult.Ok -> Unit
        }

        val (start, end) = WeekDates.dateRangeForWeekStarts(weekStarts)
        return when (val tasks = fetchTasksRange(context, start, end)) {
            is FetchResult.AuthRequired -> FetchResult.AuthRequired
            is FetchResult.Failed -> FetchResult.Ok(Unit)
            is FetchResult.Ok -> {
                val current = cachedBundle ?: DashboardCacheBundle()
                cachedBundle = current.copy(
                    tasks = mergeTasksInRange(current.tasks, tasks.value, start, end),
                )
                FetchResult.Ok(Unit)
            }
        }
    }

    private suspend fun refreshWeeksAndTasks(
        context: Context,
        weekStarts: List<String>,
    ): FetchResult<DashboardCacheBundle> {
        when (fetchAndMergeWeeks(context, weekStarts, mergeIntoExisting = true)) {
            is FetchResult.AuthRequired -> return FetchResult.AuthRequired
            is FetchResult.Failed -> if (cachedBundle == null) return FetchResult.Failed
            is FetchResult.Ok -> Unit
        }

        val (start, end) = WeekDates.dateRangeForWeekStarts(weekStarts)
        return when (val tasks = fetchTasksRange(context, start, end)) {
            is FetchResult.AuthRequired -> FetchResult.AuthRequired
            is FetchResult.Failed -> {
                cachedBundle?.let { FetchResult.Ok(it) } ?: FetchResult.Failed
            }
            is FetchResult.Ok -> {
                val bundle = cachedBundle ?: DashboardCacheBundle()
                val mergedTasks = mergeTasksInRange(bundle.tasks, tasks.value, start, end)
                val updated = bundle.copy(tasks = mergedTasks)
                cachedBundle = updated
                FetchResult.Ok(updated)
            }
        }
    }

    private fun mergeTasksInRange(
        existing: List<CachedTaskItem>,
        fresh: List<CachedTaskItem>,
        start: String,
        end: String,
    ): List<CachedTaskItem> {
        val retained = existing.filter { it.date < start || it.date > end }
        return retained + fresh
    }

    private suspend fun fetchAndMergeWeeks(
        context: Context,
        weekStarts: List<String>,
        mergeIntoExisting: Boolean = true,
    ): FetchResult<DashboardCacheBundle> {
        if (weekStarts.isEmpty()) {
            return FetchResult.Ok(cachedBundle ?: DashboardCacheBundle())
        }

        val sorted = weekStarts.sorted()
        val rangeStart = sorted.first()
        val rangeEnd = WeekDates.addDays(sorted.last(), 6)

        return when (val result = fetchDashboardRange(context, rangeStart, rangeEnd)) {
            is FetchResult.AuthRequired -> FetchResult.AuthRequired
            is FetchResult.Failed -> FetchResult.Failed
            is FetchResult.Ok -> {
                val baseWeeks = if (mergeIntoExisting) {
                    cachedBundle?.weeks?.toMutableMap() ?: mutableMapOf()
                } else {
                    mutableMapOf()
                }
                baseWeeks.putAll(result.value)
                val bundle = DashboardCacheBundle(
                    tasks = cachedBundle?.tasks ?: emptyList(),
                    weeks = baseWeeks,
                )
                cachedBundle = bundle
                FetchResult.Ok(bundle)
            }
        }
    }

    private suspend fun fetchTasksRange(
        context: Context,
        start: String,
        end: String,
    ): FetchResult<List<CachedTaskItem>> {
        return try {
            val api = ApiClient.getApi(context)
            val raw = api.getTasks(start, end, System.currentTimeMillis())
            FetchResult.Ok(
                raw.map { dto ->
                    CachedTaskItem(
                        id = dto.id,
                        title = dto.title,
                        description = dto.description ?: "",
                        icon = dto.icon ?: "default",
                        completed = dto.completed,
                        person_id = dto.person_id,
                        date = dto.date,
                    )
                },
            )
        } catch (e: HttpException) {
            if (e.code() == 401) FetchResult.AuthRequired else FetchResult.Failed
        } catch (e: Exception) {
            Log.w(TAG, "fetchTasksRange failed", e)
            FetchResult.Failed
        }
    }

    private suspend fun fetchEtag(context: Context): FetchResult<String> {
        return try {
            val api = ApiClient.getApi(context)
            FetchResult.Ok(api.getEtag(System.currentTimeMillis()).etag)
        } catch (e: HttpException) {
            if (e.code() == 401) FetchResult.AuthRequired else FetchResult.Failed
        } catch (e: Exception) {
            Log.w(TAG, "fetchEtag failed", e)
            FetchResult.Failed
        }
    }

    private suspend fun fetchDashboardRange(
        context: Context,
        startDate: String,
        endDate: String,
    ): FetchResult<Map<String, WeekCalendarData>> {
        return try {
            val api = ApiClient.getApi(context)
            val parsed = api.getDashboardRange(startDate, endDate, System.currentTimeMillis())
            val weeks = parsed.weeks
            if (weeks.isNullOrEmpty()) {
                if (parsed.weekDays != null && parsed.calendar != null) {
                    val weekStart = WeekDates.mondayOf(startDate)
                    return FetchResult.Ok(
                        mapOf(
                            weekStart to WeekCalendarData(
                                weekDays = parsed.weekDays,
                                calendar = parsed.calendar,
                            ),
                        ),
                    )
                }
                return FetchResult.Failed
            }
            FetchResult.Ok(
                weeks.associate { week ->
                    week.week_start to WeekCalendarData(
                        weekDays = week.weekDays,
                        calendar = week.calendar,
                    )
                },
            )
        } catch (e: HttpException) {
            if (e.code() == 401) FetchResult.AuthRequired else FetchResult.Failed
        } catch (e: Exception) {
            Log.w(TAG, "fetchDashboardRange failed", e)
            FetchResult.Failed
        }
    }

    private fun CachedTaskItem.toEntity() = CachedTaskEntity(
        id = id,
        title = title,
        description = description,
        icon = icon,
        completed = completed,
        personId = person_id,
        date = date,
    )

    private fun CachedTaskEntity.toCachedTaskItem() = CachedTaskItem(
        id = id,
        title = title,
        description = description,
        icon = icon,
        completed = completed,
        person_id = personId,
        date = date,
    )

    private fun WeekCalendarEntity.toWeekCalendarData(): WeekCalendarData {
        val weekDaysType = object : TypeToken<List<WeekDay>>() {}.type
        val calendarType = object : TypeToken<List<PersonCalendar>>() {}.type
        return WeekCalendarData(
            weekDays = gson.fromJson(weekDaysJson, weekDaysType),
            calendar = gson.fromJson(calendarJson, calendarType),
        )
    }

    data class LoginResult(val token: String, val person_id: Int, val name: String)
}
