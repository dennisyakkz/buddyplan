package nl.buddyplan.display

import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import nl.buddyplan.display.data.DataRepository
import nl.buddyplan.display.ui.ColorPalette
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class SettingsActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_INITIAL_TAB = "initial_tab"
        const val TAB_APPS = 0
        const val TAB_CONNECTIE = 1
        const val TAB_TAKEN = 2
        const val TAB_BEVEILIGING = 3
        const val TAB_SYSTEEM = 4
        const val TAB_UPDATES = 5
    }

    private lateinit var contentFrame: FrameLayout
    private val tabButtons = mutableListOf<Button>()

    private lateinit var updateOverlay: FrameLayout
    private lateinit var updateOverlayMessage: TextView
    private lateinit var updateOverlayStatus: TextView
    private lateinit var updateOverlayProgress: ProgressBar
    private lateinit var updateOverlayHintDuration: TextView
    private lateinit var updateOverlayHintRestart: TextView
    private lateinit var updateOverlayButtons: LinearLayout
    private lateinit var btnUpdateInstall: Button
    private lateinit var btnUpdateLater: Button
    private var pendingUpdateVersion = 0
    private var awaitingInstallPermission = false
    private var installWatchJob: Job? = null

    // Taken tab state
    private data class AppUser(val id: Int, val name: String)
    private var appUsers: List<AppUser> = emptyList()
    private val userEnabled = mutableMapOf<Int, Boolean>()
    private val userColors = mutableMapOf<Int, String>()

    /**
     * Close settings when the user presses HOME, unless an APK install is in progress.
     */
    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        if (UpgradeInstallState.isInProgress(this)) return
        finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        contentFrame = findViewById(R.id.settingsContent)

        val tabs = listOf<Button>(
            findViewById(R.id.tabApps),
            findViewById(R.id.tabConnectie),
            findViewById(R.id.tabTaken),
            findViewById(R.id.tabBeveiliging),
            findViewById(R.id.tabSysteem),
            findViewById(R.id.tabUpdates),
        )
        tabButtons.addAll(tabs)

        tabs[0].setOnClickListener { switchTab(0) }
        tabs[1].setOnClickListener { switchTab(1) }
        tabs[2].setOnClickListener { switchTab(2) }
        tabs[3].setOnClickListener { switchTab(3) }
        tabs[4].setOnClickListener { switchTab(4) }
        tabs[5].setOnClickListener { switchTab(5) }

        findViewById<Button>(R.id.btnSettingsClose).setOnClickListener { finish() }

        setupUpdateOverlay()
        UpgradeInstallFailureUi.setup(this)
        resumeInstallOverlayIfNeeded()
        UpgradeInstallFailureUi.showIfPending(this)

        // Load current user settings
        userEnabled.putAll(AppPreferences.getUserEnabled(this))
        userColors.putAll(AppPreferences.getUserColors(this))

        val initialTab = intent.getIntExtra(EXTRA_INITIAL_TAB, TAB_APPS)
        switchTab(initialTab.coerceIn(TAB_APPS, TAB_UPDATES))
    }

    override fun onResume() {
        super.onResume()
        UpgradeInstallState.reconcile(this)
        if (UpgradeInstallState.isInProgress(this)) {
            resumeInstallOverlayIfNeeded()
            return
        }
        UpgradeInstallFailureUi.showIfPending(this)
        if (awaitingInstallPermission && updateOverlay.visibility == View.VISIBLE) {
            if (DashboardUpgradeManager.canInstallPackages(this)) {
                awaitingInstallPermission = false
                btnUpdateInstall.text = getString(R.string.update_install_now)
                startPendingUpdateInstall()
            }
        }
    }

    override fun onDestroy() {
        cancelInstallWatch()
        super.onDestroy()
    }

    // -------------------------------------------------------------------------
    // Tab switching
    // -------------------------------------------------------------------------

    private fun switchTab(index: Int) {
        tabButtons.forEachIndexed { i, btn -> btn.isSelected = i == index }
        contentFrame.removeAllViews()
        val view = when (index) {
            0 -> buildAppsTab()
            1 -> buildConnectieTab()
            2 -> buildTakenTab()
            3 -> buildBeveiligingTab()
            4 -> buildSysteemTab()
            5 -> buildUpdatesTab()
            else -> return
        }
        contentFrame.addView(view)
    }

    // -------------------------------------------------------------------------
    // Tab 0 – Apps (mini launcher)
    // -------------------------------------------------------------------------

    private fun buildAppsTab(): View {
        val container = FrameLayout(this)

        // Show loading while resolving apps on a background thread.
        val loadingText = TextView(this).apply {
            text = "Apps laden…"
            textSize = 16f
            gravity = android.view.Gravity.CENTER
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
        }
        container.addView(
            loadingText,
            FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )

        lifecycleScope.launch {
            val apps = withContext(Dispatchers.IO) { resolveInstalledApps() }
            container.removeAllViews()
            container.addView(buildAppsGrid(apps))
        }

        return container
    }

    private data class AppInfo(val label: String, val packageName: String, val resolveInfo: ResolveInfo)

    private fun resolveInstalledApps(): List<AppInfo> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val resolved = packageManager.queryIntentActivities(intent, 0)
        return resolved
            .map { ri ->
                AppInfo(
                    label = ri.loadLabel(packageManager).toString(),
                    packageName = ri.activityInfo.packageName,
                    resolveInfo = ri,
                )
            }
            .filter { it.packageName != packageName } // exclude self
            .sortedBy { it.label.lowercase() }
    }

    private fun buildAppsGrid(apps: List<AppInfo>): View {
        val scroll = ScrollView(this)
        val grid = GridLayout(this).apply {
            columnCount = 4
            setPadding(dp(8), dp(8), dp(8), dp(8))
        }
        scroll.addView(grid)

        apps.forEach { app ->
            val cellSize = (resources.displayMetrics.widthPixels / 4)

            val cell = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                gravity = android.view.Gravity.CENTER
                layoutParams = GridLayout.LayoutParams().apply {
                    width = cellSize
                    height = ViewGroup.LayoutParams.WRAP_CONTENT
                }
                setPadding(dp(4), dp(8), dp(4), dp(8))
                isClickable = true
                isFocusable = true
                background = android.util.TypedValue().also {
                    theme.resolveAttribute(android.R.attr.selectableItemBackground, it, true)
                }.resourceId.takeIf { it != 0 }?.let {
                    ContextCompat.getDrawable(this@SettingsActivity, it)
                }
            }

            // App icon
            val icon = android.widget.ImageView(this).apply {
                val drawable = try {
                    app.resolveInfo.loadIcon(packageManager)
                } catch (_: Exception) { null }
                setImageDrawable(drawable)
                val iconSize = dp(48)
                layoutParams = LinearLayout.LayoutParams(iconSize, iconSize)
                scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
            }

            // App name
            val label = TextView(this).apply {
                text = app.label
                textSize = 11f
                gravity = android.view.Gravity.CENTER
                maxLines = 2
                ellipsize = android.text.TextUtils.TruncateAt.END
                setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_primary))
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                ).also { it.topMargin = dp(4) }
            }

            cell.addView(icon)
            cell.addView(label)

            cell.setOnClickListener {
                val launch = packageManager.getLaunchIntentForPackage(app.packageName)
                if (launch != null) {
                    launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    startActivity(launch)
                } else {
                    Toast.makeText(this, "Kan app niet starten", Toast.LENGTH_SHORT).show()
                }
            }

            grid.addView(cell)
        }

        return scroll
    }

    // -------------------------------------------------------------------------
    // Tab 1 – Connectie
    // -------------------------------------------------------------------------

    private fun buildConnectieTab(): View {
        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        scroll.addView(layout)

        // Server URL
        layout.addView(label("Server URL"))
        val urlInput = EditText(this).apply {
            hint = "https://..."
            setText(AppPreferences.getServerUrl(this@SettingsActivity))
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                    android.text.InputType.TYPE_TEXT_VARIATION_URI
        }
        layout.addView(urlInput)

        // Logged-in status
        val statusText = TextView(this).apply {
            val name = AppPreferences.getLoggedInName(this@SettingsActivity)
            text = if (name != null) "Ingelogd als: $name" else "Niet ingelogd"
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
            textSize = 14f
            setPadding(0, dp(8), 0, dp(16))
        }
        layout.addView(statusText)

        // Username + password for login
        layout.addView(label("Gebruikersnaam"))
        val usernameInput = EditText(this).apply { hint = "Gebruikersnaam" }
        layout.addView(usernameInput)

        layout.addView(label("Wachtwoord"))
        val passwordInput = EditText(this).apply {
            hint = "Wachtwoord"
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                    android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        }
        layout.addView(passwordInput)

        val feedbackText = TextView(this).apply {
            textSize = 14f
            setPadding(0, dp(8), 0, 0)
            visibility = View.GONE
        }
        layout.addView(feedbackText)

        val loginBtn = Button(this).apply {
            text = "Inloggen"
            setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.header_todo))
            setTextColor(Color.WHITE)
        }
        layout.addView(loginBtn)

        loginBtn.setOnClickListener {
            val newUrl = urlInput.text.toString().trimEnd('/')
            val username = usernameInput.text.toString().trim()
            val password = passwordInput.text.toString()

            if (newUrl.isNotBlank()) {
                AppPreferences.setServerUrl(this, newUrl)
                lifecycleScope.launch {
                    DataRepository.reset(this@SettingsActivity)
                }
            }

            if (username.isBlank() || password.isBlank()) {
                feedbackText.text = "Vul gebruikersnaam en wachtwoord in"
                feedbackText.setTextColor(Color.RED)
                feedbackText.visibility = View.VISIBLE
                return@setOnClickListener
            }

            loginBtn.isEnabled = false
            feedbackText.text = "Bezig met inloggen…"
            feedbackText.setTextColor(ContextCompat.getColor(this, R.color.text_secondary))
            feedbackText.visibility = View.VISIBLE

            lifecycleScope.launch {
                val result = DataRepository.login(this@SettingsActivity, username, password)
                loginBtn.isEnabled = true
                if (result != null) {
                    AppPreferences.setAuthToken(this@SettingsActivity, result.token)
                    AppPreferences.setLoggedInName(this@SettingsActivity, result.name)
                    AppPreferences.setConnectionConfigured(this@SettingsActivity, true)
                    statusText.text = "Ingelogd als: ${result.name}"
                    feedbackText.text = "Succesvol ingelogd"
                    feedbackText.setTextColor(Color.parseColor("#43A047"))
                    usernameInput.setText("")
                    passwordInput.setText("")
                    DataRepository.reset(this@SettingsActivity)
                } else {
                    feedbackText.text = "Inloggen mislukt. Controleer URL en gegevens."
                    feedbackText.setTextColor(Color.RED)
                }
                feedbackText.visibility = View.VISIBLE
            }
        }

        return scroll
    }

    // -------------------------------------------------------------------------
    // Tab 1 – Taken
    // -------------------------------------------------------------------------

    private fun buildTakenTab(): View {
        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        scroll.addView(layout)

        val loadingText = TextView(this).apply {
            text = "Gebruikers ophalen…"
            textSize = 16f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
        }
        layout.addView(loadingText)

        lifecycleScope.launch {
            val users = DataRepository.fetchAppUsers(this@SettingsActivity)
            layout.removeAllViews()
            if (users == null) {
                layout.addView(TextView(this@SettingsActivity).apply {
                    text = "Ophalen mislukt. Controleer server-URL en login."
                    textSize = 16f
                    setTextColor(Color.RED)
                })
                return@launch
            }
            if (users.isEmpty()) {
                layout.addView(TextView(this@SettingsActivity).apply {
                    text = "Geen gebruikers met takensysteem gevonden."
                    textSize = 16f
                    setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
                })
                return@launch
            }

            appUsers = users.map { AppUser(it.first, it.second) }
            val ids = appUsers.map { it.id }
            AppPreferences.ensureDefaultColors(this@SettingsActivity, ids)
            userColors.putAll(AppPreferences.getUserColors(this@SettingsActivity))
            ids.forEach { id ->
                if (!userEnabled.containsKey(id)) userEnabled[id] = true
            }

            appUsers.forEach { user -> layout.addView(buildUserRow(user)) }
        }

        return scroll
    }

    private fun buildUserRow(user: AppUser): View {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 0, 0, dp(16))
        }

        val topRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        // Name
        val nameText = TextView(this).apply {
            text = user.name
            textSize = 18f
            setTypeface(nl.buddyplan.display.ui.FontHelper.headingSemiBold(this@SettingsActivity), android.graphics.Typeface.BOLD)
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_primary))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        topRow.addView(nameText)

        // Toggle
        val toggle = Switch(this).apply {
            isChecked = userEnabled[user.id] ?: true
            setOnCheckedChangeListener { _, checked ->
                userEnabled[user.id] = checked
                AppPreferences.setUserEnabled(this@SettingsActivity, userEnabled.toMap())
            }
        }
        topRow.addView(toggle)
        row.addView(topRow)

        // Color swatches
        val colorRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(8), 0, 0)
            gravity = Gravity.START
        }

        var selectedSwatch: View? = null
        val currentLabel = userColors[user.id]?.let { ColorPalette.migrateStoredColor(it) }

        ColorPalette.LABELS.forEach { label ->
            val swatch = View(this).apply {
                val size = dp(36)
                layoutParams = LinearLayout.LayoutParams(size, size).also { it.setMargins(0, 0, dp(8), 0) }
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    setColor(ColorPalette.swatchPreviewColor(label))
                    if (label == currentLabel) {
                        setStroke(dp(3), Color.BLACK)
                    }
                }
            }
            if (label == currentLabel) selectedSwatch = swatch

            swatch.setOnClickListener {
                selectedSwatch?.background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    val prevLabel = (selectedSwatch?.tag as? String) ?: label
                    setColor(ColorPalette.swatchPreviewColor(prevLabel))
                }
                (swatch.background as? GradientDrawable)?.setStroke(dp(3), Color.BLACK)
                selectedSwatch = swatch

                userColors[user.id] = label
                AppPreferences.setUserColors(this, userColors.toMap())
            }
            swatch.tag = label
            colorRow.addView(swatch)
        }

        row.addView(colorRow)

        // Divider
        val divider = View(this).apply {
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(1)).also {
                it.topMargin = dp(16)
            }
            setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.divider))
        }
        row.addView(divider)

        return row
    }

    // -------------------------------------------------------------------------
    // Tab 2 – Beveiliging
    // -------------------------------------------------------------------------

    private fun buildBeveiligingTab(): View {
        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        scroll.addView(layout)

        var pinEnabled = AppPreferences.isPinEnabled(this)

        // Toggle row
        val toggleRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, dp(24))
        }
        val toggleLabel = TextView(this).apply {
            text = "Instellingen beveiligen met pincode"
            textSize = 17f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_primary))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        val pinToggle = Switch(this).apply { isChecked = pinEnabled }
        toggleRow.addView(toggleLabel)
        toggleRow.addView(pinToggle)
        layout.addView(toggleRow)

        // PIN input section
        val pinSection = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            visibility = if (pinEnabled) View.VISIBLE else View.GONE
        }

        pinSection.addView(label("Pincode (4 cijfers)"))
        val pinInput = EditText(this).apply {
            hint = "••••"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            maxEms = 4
        }
        pinSection.addView(pinInput)

        val savePinBtn = Button(this).apply {
            text = "Pincode opslaan"
            setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.header_todo))
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).also { it.topMargin = dp(12) }
        }
        pinSection.addView(savePinBtn)

        val pinFeedback = TextView(this).apply {
            textSize = 14f
            visibility = View.GONE
        }
        pinSection.addView(pinFeedback)

        layout.addView(pinSection)

        pinToggle.setOnCheckedChangeListener { _, checked ->
            pinEnabled = checked
            pinSection.visibility = if (checked) View.VISIBLE else View.GONE
            if (!checked) {
                AppPreferences.setPinEnabled(this, false)
                AppPreferences.setPinCode(this, "")
            }
        }

        savePinBtn.setOnClickListener {
            val pin = pinInput.text.toString().trim()
            if (pin.length != 4 || !pin.all { it.isDigit() }) {
                pinFeedback.text = "Voer een geldige 4-cijferige pincode in"
                pinFeedback.setTextColor(Color.RED)
                pinFeedback.visibility = View.VISIBLE
                return@setOnClickListener
            }
            AppPreferences.setPinEnabled(this, true)
            AppPreferences.setPinCode(this, pin)
            pinFeedback.text = "Pincode opgeslagen"
            pinFeedback.setTextColor(Color.parseColor("#43A047"))
            pinFeedback.visibility = View.VISIBLE
            pinInput.setText("")
        }

        return scroll
    }

    // -------------------------------------------------------------------------
    // Tab 3 – Systeem
    // -------------------------------------------------------------------------

    private fun buildSysteemTab(): View {
        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
            gravity = Gravity.TOP
        }
        scroll.addView(layout)

        // Dark mode toggle (first option)
        layout.addView(buildToggleRow(
            labelText = "Donkere modus",
            isChecked = AppPreferences.isDarkMode(this),
            onChanged = { enabled ->
                AppPreferences.setDarkMode(this, enabled)
                BuddyplanDisplayApp.applyDarkMode(this)
                // Recreate both this activity and signal MainActivity to do the same.
                recreate()
            }
        ))

        layout.addView(divider())

        // System settings button
        val sysBtn = Button(this).apply {
            text = "Systeeminstellingen openen"
            setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.header_todo))
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).also { it.topMargin = dp(16); it.bottomMargin = dp(16) }
        }
        sysBtn.setOnClickListener { startActivity(Intent(Settings.ACTION_SETTINGS)) }
        layout.addView(sysBtn)

        // Set as launcher button
        val isAlreadyLauncher = isDefaultLauncher()
        val launcherBtn = Button(this).apply {
            text = if (isAlreadyLauncher) "App is al de standaard launcher" else "Instellen als launcher"
            isEnabled = !isAlreadyLauncher
            setBackgroundColor(
                if (isAlreadyLauncher)
                    ContextCompat.getColor(this@SettingsActivity, R.color.divider)
                else
                    ContextCompat.getColor(this@SettingsActivity, R.color.button_done)
            )
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }
        launcherBtn.setOnClickListener {
            val intent = Intent(Intent.ACTION_MAIN).apply {
                addCategory(Intent.CATEGORY_HOME)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            startActivity(intent)
        }
        layout.addView(launcherBtn)

        return scroll
    }

    // -------------------------------------------------------------------------
    // Tab 5 – Updates
    // -------------------------------------------------------------------------

    private fun buildUpdatesTab(): View {
        val scroll = ScrollView(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(24), dp(24), dp(24))
        }
        scroll.addView(layout)

        layout.addView(TextView(this).apply {
            text = "Controleer op updates"
            textSize = 20f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_primary))
            setPadding(0, 0, 0, dp(16))
        })

        val installedVersion = AppPreferences.getInstalledUpgradeVersion(this)
        val versionInfo = TextView(this).apply {
            text = "Geïnstalleerde versie: $installedVersion"
            textSize = 14f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
            setPadding(0, 0, 0, dp(16))
        }
        layout.addView(versionInfo)

        val statusText = TextView(this).apply {
            textSize = 15f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
            visibility = View.GONE
        }
        layout.addView(statusText)

        val checkBtn = Button(this).apply {
            text = "Controleer op updates"
            setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.header_todo))
            setTextColor(Color.WHITE)
        }
        layout.addView(checkBtn)

        checkBtn.setOnClickListener {
            if (AppPreferences.getAuthToken(this).isNullOrBlank()) {
                statusText.text = "Log eerst in via de tab Connectie."
                statusText.setTextColor(Color.RED)
                statusText.visibility = View.VISIBLE
                return@setOnClickListener
            }

            checkBtn.isEnabled = false
            statusText.text = "Bezig met controleren…"
            statusText.setTextColor(ContextCompat.getColor(this, R.color.text_secondary))
            statusText.visibility = View.VISIBLE

            lifecycleScope.launch {
                val info = DashboardUpgradeManager.fetchServerUpgrade(this@SettingsActivity)
                checkBtn.isEnabled = true

                if (info == null) {
                    statusText.text = "Controleren mislukt. Controleer server-URL en login."
                    statusText.setTextColor(Color.RED)
                    return@launch
                }

                versionInfo.text = "Geïnstalleerde versie: ${AppPreferences.getInstalledUpgradeVersion(this@SettingsActivity)}"

                if (info.version <= 0) {
                    statusText.text = "Er staat nog geen update op de server."
                    statusText.setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
                    return@launch
                }

                if (DashboardUpgradeManager.isUpdateAvailable(this@SettingsActivity, info.version)) {
                    val uploadedAt = info.uploadedAt?.let { formatUpgradeDate(it) } ?: "onbekend"
                    showUpdateLightbox(
                        info.version,
                        "Er is een nieuwe versie beschikbaar (versie ${info.version}, geüpload op $uploadedAt).",
                    )
                    statusText.text = "Update beschikbaar."
                    statusText.setTextColor(Color.parseColor("#43A047"))
                } else {
                    statusText.text = "Je gebruikt de nieuwste versie."
                    statusText.setTextColor(Color.parseColor("#43A047"))
                }
            }
        }

        return scroll
    }

    private fun setupUpdateOverlay() {
        updateOverlay = findViewById(R.id.updateOverlay)
        updateOverlayMessage = findViewById(R.id.updateOverlayMessage)
        updateOverlayStatus = findViewById(R.id.updateOverlayStatus)
        updateOverlayProgress = findViewById(R.id.updateOverlayProgress)
        updateOverlayHintDuration = findViewById(R.id.updateOverlayHintDuration)
        updateOverlayHintRestart = findViewById(R.id.updateOverlayHintRestart)
        updateOverlayButtons = findViewById(R.id.updateOverlayButtons)
        btnUpdateInstall = findViewById(R.id.btnUpdateInstall)
        btnUpdateLater = findViewById(R.id.btnUpdateLater)

        updateOverlay.setOnClickListener {
            if (!UpgradeInstallState.isInProgress(this)) hideUpdateLightbox()
        }
        findViewById<LinearLayout>(R.id.updateOverlayDialog).setOnClickListener { }
        btnUpdateLater.setOnClickListener {
            if (!UpgradeInstallState.isInProgress(this)) hideUpdateLightbox()
        }
        btnUpdateInstall.setOnClickListener { startPendingUpdateInstall() }
    }

    private fun resumeInstallOverlayIfNeeded() {
        if (!UpgradeInstallState.isInProgress(this)) return

        val version = AppPreferences.getPendingUpgradeVersion(this)
        if (version > 0) {
            pendingUpdateVersion = version
            updateOverlayMessage.text = "Update naar versie $version wordt geïnstalleerd."
        }
        updateOverlay.visibility = View.VISIBLE
        applyInstallProgressUi()
        startInstallWatch()
    }

    private fun applyInstallProgressUi() {
        val installing = UpgradeInstallState.isInstalling(this)
        val statusText = if (installing) {
            getString(R.string.update_install_in_progress)
        } else {
            getString(R.string.update_install_awaiting_confirm)
        }
        updateOverlayStatus.text = statusText
        updateOverlayStatus.setTextColor(ContextCompat.getColor(this, R.color.text_secondary))
        updateOverlayStatus.visibility = View.VISIBLE
        updateOverlayProgress.visibility = if (installing) View.VISIBLE else View.GONE
        updateOverlayHintDuration.visibility = if (installing) View.VISIBLE else View.GONE
        updateOverlayHintRestart.visibility = if (installing) View.VISIBLE else View.GONE
        updateOverlayButtons.visibility = View.GONE
    }

    private fun startInstallWatch() {
        cancelInstallWatch()
        val deadline = UpgradeInstallState.getDeadlineMs(this) ?: return
        installWatchJob = lifecycleScope.launch {
            val delayMs = (deadline - System.currentTimeMillis()).coerceAtLeast(0L)
            delay(delayMs)
            if (!isActive) return@launch
            UpgradeInstallState.reconcile(this@SettingsActivity)
            if (!UpgradeInstallState.isInProgress(this@SettingsActivity)) {
                handleInstallTimedOut()
            }
        }
    }

    private fun cancelInstallWatch() {
        installWatchJob?.cancel()
        installWatchJob = null
    }

    private fun handleInstallTimedOut() {
        updateOverlayProgress.visibility = View.GONE
        updateOverlayHintDuration.visibility = View.GONE
        updateOverlayHintRestart.visibility = View.GONE
        updateOverlayStatus.text = getString(R.string.update_install_timeout)
        updateOverlayStatus.setTextColor(Color.RED)
        updateOverlayStatus.visibility = View.VISIBLE
        updateOverlayButtons.visibility = View.VISIBLE
        btnUpdateInstall.isEnabled = true
        btnUpdateLater.isEnabled = true
    }

    private fun showUpdateLightbox(version: Int, message: String) {
        pendingUpdateVersion = version
        updateOverlayMessage.text = message
        updateOverlayStatus.visibility = View.GONE
        updateOverlayStatus.text = ""
        updateOverlayHintDuration.visibility = View.GONE
        updateOverlayHintRestart.visibility = View.GONE
        updateOverlayButtons.visibility = View.VISIBLE
        btnUpdateInstall.isEnabled = true
        btnUpdateLater.isEnabled = true
        updateOverlay.visibility = View.VISIBLE
    }

    private fun hideUpdateLightbox() {
        if (UpgradeInstallState.isInProgress(this)) return
        cancelInstallWatch()
        awaitingInstallPermission = false
        btnUpdateInstall.text = getString(R.string.update_install_now)
        updateOverlay.visibility = View.GONE
        updateOverlayStatus.visibility = View.GONE
        updateOverlayProgress.visibility = View.GONE
        updateOverlayHintDuration.visibility = View.GONE
        updateOverlayHintRestart.visibility = View.GONE
        updateOverlayButtons.visibility = View.VISIBLE
        btnUpdateInstall.isEnabled = true
        btnUpdateLater.isEnabled = true
    }

    private fun startPendingUpdateInstall() {
        if (pendingUpdateVersion <= 0) return

        if (!DashboardUpgradeManager.canInstallPackages(this)) {
            awaitingInstallPermission = true
            btnUpdateInstall.text = getString(R.string.update_open_settings)
            updateOverlayStatus.text = getString(R.string.update_permission_required)
            updateOverlayStatus.setTextColor(Color.RED)
            updateOverlayStatus.visibility = View.VISIBLE
            if (!DashboardUpgradeManager.openInstallPermissionSettings(this)) {
                updateOverlayStatus.text = getString(R.string.update_permission_settings_failed)
            }
            return
        }

        awaitingInstallPermission = false
        btnUpdateInstall.text = getString(R.string.update_install_now)

        updateOverlayButtons.visibility = View.GONE
        btnUpdateInstall.isEnabled = false
        btnUpdateLater.isEnabled = false
        updateOverlayProgress.visibility = View.GONE
        updateOverlayHintDuration.visibility = View.GONE
        updateOverlayHintRestart.visibility = View.GONE
        updateOverlayStatus.text = getString(R.string.update_downloading)
        updateOverlayStatus.setTextColor(ContextCompat.getColor(this, R.color.text_secondary))
        updateOverlayStatus.visibility = View.VISIBLE

        lifecycleScope.launch {
            val apkFile = DashboardUpgradeManager.downloadApk(this@SettingsActivity)
            if (apkFile == null) {
                UpgradeInstallState.clear(this@SettingsActivity)
                updateOverlayStatus.text = getString(R.string.update_download_failed)
                updateOverlayStatus.setTextColor(Color.RED)
                updateOverlayButtons.visibility = View.VISIBLE
                btnUpdateInstall.isEnabled = true
                btnUpdateLater.isEnabled = true
                return@launch
            }

            when (val result = DashboardUpgradeManager.installApk(this@SettingsActivity, apkFile, pendingUpdateVersion)) {
                is DashboardUpgradeManager.InstallResult.Started -> {
                    applyInstallProgressUi()
                    startInstallWatch()
                }
                is DashboardUpgradeManager.InstallResult.Failed -> {
                    UpgradeInstallState.clear(this@SettingsActivity)
                    updateOverlayStatus.text = result.message
                    updateOverlayStatus.setTextColor(Color.RED)
                    updateOverlayProgress.visibility = View.GONE
                    updateOverlayHintDuration.visibility = View.GONE
                    updateOverlayHintRestart.visibility = View.GONE
                    updateOverlayButtons.visibility = View.VISIBLE
                    btnUpdateInstall.isEnabled = true
                    btnUpdateLater.isEnabled = true
                }
            }
        }
    }

    private fun formatUpgradeDate(iso: String): String {
        return try {
            val parser = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.getDefault())
            parser.timeZone = java.util.TimeZone.getTimeZone("UTC")
            val date = parser.parse(iso.take(19)) ?: return iso
            val formatter = java.text.SimpleDateFormat("dd-MM-yyyy HH:mm", java.util.Locale.getDefault())
            formatter.format(date)
        } catch (_: Exception) {
            iso
        }
    }

    private fun buildToggleRow(
        labelText: String,
        isChecked: Boolean,
        onChanged: (Boolean) -> Unit
    ): View {
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(8), 0, dp(8))
        }
        val lbl = TextView(this).apply {
            text = labelText
            textSize = 17f
            setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_primary))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        val toggle = Switch(this).apply {
            this.isChecked = isChecked
            setOnCheckedChangeListener { _, checked -> onChanged(checked) }
        }
        row.addView(lbl)
        row.addView(toggle)
        return row
    }

    private fun divider() = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(1)
        ).also { it.topMargin = dp(8); it.bottomMargin = dp(8) }
        setBackgroundColor(ContextCompat.getColor(this@SettingsActivity, R.color.divider))
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private fun isDefaultLauncher(): Boolean {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
        val info = packageManager.resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY)
        return info?.activityInfo?.packageName == packageName
    }

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        textSize = 14f
        setTextColor(ContextCompat.getColor(this@SettingsActivity, R.color.text_secondary))
        layoutParams = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        ).also { it.topMargin = dp(16); it.bottomMargin = dp(4) }
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
}
