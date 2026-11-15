plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "nl.buddyplan.display"
    compileSdk = 34

    defaultConfig {
        applicationId = "nl.buddyplan.display"
        minSdk = 23
        targetSdk = 33
        versionCode = 703
        versionName = "0.7.3"
    }

    // The signing key never lives in this (public) repo. Put BUDDYPLAN_KEYSTORE,
    // BUDDYPLAN_KEYSTORE_PASSWORD, BUDDYPLAN_KEY_ALIAS and BUDDYPLAN_KEY_PASSWORD in
    // ~/.gradle/gradle.properties (or the environment). Debug builds use the same key when it is
    // configured, so a test APK installs over the release app on the tablet and vice versa.
    val releaseSigning = signingConfigs.create("buddyplan").takeIf { configureBuddyplanSigning(it) }

    buildTypes {
        debug {
            releaseSigning?.let { signingConfig = it }
        }
        release {
            isMinifyEnabled = false
            signingConfig = releaseSigning
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.core:core-ktx:1.10.1")
    implementation("androidx.recyclerview:recyclerview:1.3.0")
    implementation("androidx.cardview:cardview:1.0.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("com.google.android.material:material:1.9.0")
    implementation("com.google.code.gson:gson:2.10.1")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.2")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.activity:activity-ktx:1.7.2")

    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
}

fun signingValue(name: String): String? =
    (project.findProperty(name) as String?)?.takeIf { it.isNotBlank() } ?: System.getenv(name)?.takeIf { it.isNotBlank() }

fun configureBuddyplanSigning(config: com.android.build.api.dsl.ApkSigningConfig): Boolean {
    val keystore = signingValue("BUDDYPLAN_KEYSTORE") ?: return false
    config.storeFile = file(keystore)
    config.storePassword = signingValue("BUDDYPLAN_KEYSTORE_PASSWORD")
    config.keyAlias = signingValue("BUDDYPLAN_KEY_ALIAS")
    config.keyPassword = signingValue("BUDDYPLAN_KEY_PASSWORD")
    return true
}

// Fail loudly instead of producing an unsigned (uninstallable) release APK.
gradle.taskGraph.whenReady {
    if (signingValue("BUDDYPLAN_KEYSTORE") == null && allTasks.any { it.name.startsWith("assembleRelease") || it.name.startsWith("bundleRelease") }) {
        throw GradleException(
            "Release builds need the Buddyplan signing key: set BUDDYPLAN_KEYSTORE, " +
                "BUDDYPLAN_KEYSTORE_PASSWORD, BUDDYPLAN_KEY_ALIAS and BUDDYPLAN_KEY_PASSWORD in " +
                "~/.gradle/gradle.properties (see README).",
        )
    }
}
