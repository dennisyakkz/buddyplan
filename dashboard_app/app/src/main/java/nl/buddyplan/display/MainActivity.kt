package nl.buddyplan.display

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import nl.buddyplan.display.data.ConnectionState
import nl.buddyplan.display.data.DayCalendarEvent
import nl.buddyplan.display.data.TodoItem
import nl.buddyplan.display.data.WeekDay
import nl.buddyplan.display.data.PersonCalendar
import nl.buddyplan.display.data.WeekDates
import nl.buddyplan.display.ui.CalendarViewBuilder
import nl.buddyplan.display.ui.DayViewBuilder
import nl.buddyplan.display.ui.SwipeNavLayout
import nl.buddyplan.display.ui.TodoAdapter
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private val viewModel: DashboardViewModel by viewModels()

    private lateinit var todoAdapter: TodoAdapter
    private var selectedTodo: TodoItem? = null

    private lateinit var taskOverlay: FrameLayout
    private lateinit var popupIcon: TextView
    private lateinit var popupTitle: TextView
    private lateinit var popupDescription: TextView
    private lateinit var buttonDone: Button
    private lateinit var buttonClose: ImageButton
    private lateinit var calendarContainer: LinearLayout

    private lateinit var calWeekHeader: LinearLayout
    private lateinit var calendarSwipeArea: SwipeNavLayout
    private lateinit var dayViewPanel: LinearLayout
    private lateinit var dayViewDateTitle: TextView
    private lateinit var dayViewListContainer: FrameLayout

    private lateinit var btnCalPrev: Button
    private lateinit var btnCalToday: Button
    private lateinit var btnCalNext: Button

    private lateinit var loadingOverlay: FrameLayout
    private lateinit var installOverlay: FrameLayout
    private lateinit var installOverlayMessage: TextView
    private lateinit var installOverlayProgress: ProgressBar
    private lateinit var installOverlayHintDuration: TextView
    private lateinit var installOverlayHintRestart: TextView
    private lateinit var connectionStatus: FrameLayout
    private lateinit var connectionStatusIcon: ImageView
    private lateinit var connectionStatusSpinner: ProgressBar

    private var settingsOpenedForSetup = false
    private var currentWeekDays: List<WeekDay> = emptyList()
    private var currentCalendarPeople: List<PersonCalendar> = emptyList()
    private var dayViewOpen = false
    private var dayViewDayIndex = -1
    private var dayViewWeekDay: WeekDay? = null
    private var dayViewPersonFilter: String? = null
    private var dayViewAutoCloseJob: Job? = null
    private var installWatchJob: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        enableFullscreen()

        calendarContainer = findViewById(R.id.calendarContainer)
        calWeekHeader = findViewById(R.id.calWeekHeader)
        calendarSwipeArea = findViewById(R.id.calendarSwipeArea)
        dayViewPanel = findViewById(R.id.dayViewPanel)
        dayViewDateTitle = findViewById(R.id.dayViewDateTitle)
        dayViewListContainer = findViewById(R.id.dayViewListContainer)
        btnCalPrev = findViewById(R.id.btnCalPrev)
        btnCalToday = findViewById(R.id.btnCalToday)
        btnCalNext = findViewById(R.id.btnCalNext)

        loadingOverlay = findViewById(R.id.loadingOverlay)
        installOverlay = findViewById(R.id.installOverlay)
        installOverlayMessage = findViewById(R.id.installOverlayMessage)
        installOverlayProgress = findViewById(R.id.installOverlayProgress)
        installOverlayHintDuration = findViewById(R.id.installOverlayHintDuration)
        installOverlayHintRestart = findViewById(R.id.installOverlayHintRestart)
        connectionStatus = findViewById(R.id.connectionStatus)
        connectionStatusIcon = findViewById(R.id.connectionStatusIcon)
        connectionStatusSpinner = findViewById(R.id.connectionStatusSpinner)

        viewModel.initialize()

        setupOverlay()
        setupCalendarNav()
        setupCalendarSwipe()
        setupDayView()
        setupSettingsButton()
        setupConnectionStatus()
        observeUiState()
        UpgradeInstallFailureUi.setup(this)
        SessionExpiredUi.setup(this) {
            SessionExpiredUi.clearSession(this)
            SessionExpiredUi.navigateToLogin(this)
        }
        refreshInstallOverlay()
        UpgradeInstallFailureUi.showIfPending(this)
    }

    override fun onDestroy() {
        cancelInstallWatch()
        super.onDestroy()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) enableFullscreen()
    }

    override fun onResume() {
        super.onResume()

        BuddyplanDisplayApp.applyDarkMode(this)
        val nightMode = resources.configuration.uiMode and
                android.content.res.Configuration.UI_MODE_NIGHT_MASK
        val wantDark = AppPreferences.isDarkMode(this)
        val isDark = nightMode == android.content.res.Configuration.UI_MODE_NIGHT_YES
        if (wantDark != isDark) {
            recreate()
            return
        }

        if (::todoAdapter.isInitialized) {
            todoAdapter.updateUserSettings(
                AppPreferences.getUserColors(this),
                AppPreferences.getUserEnabled(this),
            )
        }

        refreshInstallOverlay()
        UpgradeInstallFailureUi.showIfPending(this)

        if (!AppPreferences.getAuthToken(this).isNullOrBlank()) {
            SessionExpiredUi.dismiss(this)
            viewModel.clearAuthRequired()
        }

        val isConnectionConfigured = AppPreferences.isConnectionConfigured(this)
        viewModel.onResume(isConnectionConfigured, settingsOpenedForSetup) {
            settingsOpenedForSetup = true
            loadingOverlay.visibility = View.GONE
            connectionStatus.visibility = View.GONE
            openSettings(forSetup = true)
        }
    }

    private fun observeUiState() {
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    state.dashboard?.let { applyDashboard(it) }

                    when (state.connectionState) {
                        ConnectionState.Connected -> {
                            connectionStatus.visibility = View.GONE
                        }
                        ConnectionState.Offline -> {
                            loadingOverlay.visibility = View.GONE
                            connectionStatus.visibility = View.VISIBLE
                            connectionStatusIcon.visibility = View.VISIBLE
                            connectionStatusSpinner.visibility = View.GONE
                            connectionStatus.isClickable = true
                        }
                        ConnectionState.Syncing -> {
                            loadingOverlay.visibility = View.GONE
                            connectionStatus.visibility = View.VISIBLE
                            connectionStatusIcon.visibility = View.GONE
                            connectionStatusSpinner.visibility = View.VISIBLE
                            connectionStatus.isClickable = false
                        }
                    }

                    if (state.authRequired) {
                        val shouldShow = AppPreferences.getAuthToken(this@MainActivity).isNullOrBlank()
                        viewModel.clearAuthRequired()
                        if (shouldShow) {
                            SessionExpiredUi.show(this@MainActivity)
                        }
                    }
                }
            }
        }
    }

    private fun setupConnectionStatus() {
        connectionStatus.setOnClickListener {
            viewModel.forceSync()
        }
    }

    private fun applyDashboard(data: nl.buddyplan.display.data.DashboardData) {
        loadingOverlay.visibility = View.GONE
        setupTodoList(data.todo)
        setupCalendar(data.weekDays, data.calendar)
        if (dayViewOpen) {
            refreshDayViewContent()
        }
    }

    private fun enableFullscreen() {
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            val decorView = window.decorView
            val flags = (View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    or View.SYSTEM_UI_FLAG_FULLSCREEN
                    or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY)
            decorView.systemUiVisibility = flags
        } else {
            @Suppress("DEPRECATION")
            window.setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN
            )
        }
    }

    private fun setupTodoList(todos: List<TodoItem>) {
        val recyclerView = findViewById<RecyclerView>(R.id.todoRecyclerView)
        if (!::todoAdapter.isInitialized) {
            todoAdapter = TodoAdapter { item -> showTaskOverlay(item) }
            recyclerView.layoutManager = LinearLayoutManager(this)
            recyclerView.adapter = todoAdapter
            todoAdapter.updateUserSettings(
                AppPreferences.getUserColors(this),
                AppPreferences.getUserEnabled(this),
            )
        }
        todoAdapter.submitList(todos)
    }

    private fun setupSettingsButton() {
        findViewById<TextView>(R.id.btnSettings).setOnClickListener {
            val hasToken = !AppPreferences.getAuthToken(this).isNullOrBlank()
            if (hasToken && AppPreferences.isPinEnabled(this)) {
                val pin = AppPreferences.getPinCode(this)
                PinEntryDialog(this, pin, onSuccess = { openSettings() }).show()
            } else {
                openSettings()
            }
        }
    }

    private fun openSettings(forSetup: Boolean = false) {
        val intent = Intent(this, SettingsActivity::class.java)
        if (forSetup) {
            intent.putExtra(SettingsActivity.EXTRA_INITIAL_TAB, SettingsActivity.TAB_CONNECTIE)
        }
        startActivity(intent)
    }

    private fun setupCalendar(weekDays: List<WeekDay>, people: List<PersonCalendar>) {
        currentWeekDays = weekDays
        currentCalendarPeople = people
        CalendarViewBuilder.build(
            context = this,
            container = calendarContainer,
            weekDays = weekDays,
            people = people,
            todayIso = WeekDates.todayIso(),
            onDayHeaderClick = { dayIndex, weekDay -> openDayView(dayIndex, weekDay, null) },
            onPersonDayClick = { dayIndex, weekDay, person ->
                openDayView(dayIndex, weekDay, person.name)
            },
        )
    }

    private fun setupDayView() {
        findViewById<Button>(R.id.btnDayViewBack).setOnClickListener { closeDayView() }
    }

    private fun openDayView(dayIndex: Int, weekDay: WeekDay, personFilter: String?) {
        dayViewOpen = true
        dayViewDayIndex = dayIndex
        dayViewWeekDay = weekDay
        dayViewPersonFilter = personFilter

        calWeekHeader.visibility = View.GONE
        calendarSwipeArea.visibility = View.GONE
        dayViewPanel.visibility = View.VISIBLE
        dayViewDateTitle.text = DayViewBuilder.formatDayHeader(weekDay)
        refreshDayViewContent()
        scheduleDayViewAutoClose()
    }

    private fun closeDayView() {
        dayViewAutoCloseJob?.cancel()
        dayViewAutoCloseJob = null
        dayViewOpen = false
        dayViewDayIndex = -1
        dayViewWeekDay = null
        dayViewPersonFilter = null

        dayViewPanel.visibility = View.GONE
        calWeekHeader.visibility = View.VISIBLE
        calendarSwipeArea.visibility = View.VISIBLE
        dayViewListContainer.removeAllViews()
    }

    private fun refreshDayViewContent() {
        val weekDay = dayViewWeekDay ?: return
        val events = collectDayEvents(dayViewDayIndex, dayViewPersonFilter)
        val listContent = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        DayViewBuilder.buildList(this, listContent, events)
        dayViewListContainer.removeAllViews()
        dayViewListContainer.addView(DayViewBuilder.wrapInScrollView(this, listContent))
        dayViewDateTitle.text = DayViewBuilder.formatDayHeader(weekDay)
    }

    private fun collectDayEvents(dayIndex: Int, personFilter: String?): List<DayCalendarEvent> {
        val people = if (personFilter.isNullOrBlank()) {
            currentCalendarPeople
        } else {
            currentCalendarPeople.filter { it.name == personFilter }
        }
        return people.flatMap { person ->
            person.eventsForDay(dayIndex).map { item ->
                DayCalendarEvent(person.name, item)
            }
        }.sortedWith(
            compareBy(
                { it.item.dayViewSortOrder() },
                { it.item.dayViewSortTime() },
                { it.item.displayTitle().lowercase() },
            ),
        )
    }

    private fun scheduleDayViewAutoClose() {
        dayViewAutoCloseJob?.cancel()
        dayViewAutoCloseJob = lifecycleScope.launch {
            delay(120_000)
            if (dayViewOpen) {
                closeDayView()
            }
        }
    }

    private fun setupOverlay() {
        taskOverlay = findViewById(R.id.taskOverlay)
        popupIcon = findViewById(R.id.popupIcon)
        popupTitle = findViewById(R.id.popupTitle)
        popupDescription = findViewById(R.id.popupDescription)
        buttonDone = findViewById(R.id.buttonDone)
        buttonClose = findViewById(R.id.buttonClose)

        buttonClose.setOnClickListener { hideTaskOverlay() }
        buttonDone.setOnClickListener {
            selectedTodo?.let { todo ->
                if (!todo.completed) {
                    todoAdapter.markCompleted(todo.id)
                    viewModel.reportCompletion(todo.id)
                }
            }
            hideTaskOverlay()
        }
        taskOverlay.setOnClickListener { hideTaskOverlay() }
    }

    private fun setupCalendarNav() {
        btnCalPrev.setOnClickListener {
            closeDayView()
            viewModel.navigateWeek(-1)
        }
        btnCalNext.setOnClickListener {
            closeDayView()
            viewModel.navigateWeek(1)
        }
        btnCalToday.setOnClickListener {
            closeDayView()
            viewModel.goToToday()
        }
    }

    private fun setupCalendarSwipe() {
        calendarSwipeArea.onSwipeToPrevious = {
            closeDayView()
            viewModel.navigateWeek(-1)
        }
        calendarSwipeArea.onSwipeToNext = {
            closeDayView()
            viewModel.navigateWeek(1)
        }
    }

    private fun showTaskOverlay(item: TodoItem) {
        if (item.completed) return
        selectedTodo = item
        FaIconHelper.applyIcon(popupIcon, item.icon, 72f)
        popupTitle.text = item.title
        popupDescription.text = item.description
        buttonDone.visibility = View.VISIBLE
        taskOverlay.visibility = View.VISIBLE
    }

    private fun hideTaskOverlay() {
        taskOverlay.visibility = View.GONE
        selectedTodo = null
    }

    private fun refreshInstallOverlay() {
        UpgradeInstallState.reconcile(this)
        if (!UpgradeInstallState.isInProgress(this)) {
            hideInstallOverlay()
            return
        }

        val version = AppPreferences.getPendingUpgradeVersion(this)
        val installing = UpgradeInstallState.isInstalling(this)
        installOverlayMessage.text = if (installing) {
            if (version > 0) {
                getString(R.string.update_install_in_progress_version, version)
            } else {
                getString(R.string.update_install_in_progress)
            }
        } else {
            getString(R.string.update_install_awaiting_confirm)
        }
        installOverlayProgress.visibility = if (installing) View.VISIBLE else View.GONE
        installOverlayHintDuration.visibility = if (installing) View.VISIBLE else View.GONE
        installOverlayHintRestart.visibility = if (installing) View.VISIBLE else View.GONE
        installOverlay.visibility = View.VISIBLE
        startInstallWatch()
    }

    private fun hideInstallOverlay() {
        cancelInstallWatch()
        installOverlay.visibility = View.GONE
        installOverlayProgress.visibility = View.GONE
        installOverlayHintDuration.visibility = View.GONE
        installOverlayHintRestart.visibility = View.GONE
    }

    private fun startInstallWatch() {
        cancelInstallWatch()
        val deadline = UpgradeInstallState.getDeadlineMs(this) ?: return
        installWatchJob = lifecycleScope.launch {
            val delayMs = (deadline - System.currentTimeMillis()).coerceAtLeast(0L)
            delay(delayMs)
            if (!isActive) return@launch
            UpgradeInstallState.reconcile(this@MainActivity)
            if (!UpgradeInstallState.isInProgress(this@MainActivity)) {
                hideInstallOverlay()
            }
        }
    }

    private fun cancelInstallWatch() {
        installWatchJob?.cancel()
        installWatchJob = null
    }
}
