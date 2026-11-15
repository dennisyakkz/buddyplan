plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "nl.buddyplan.mobile"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "nl.buddyplan.mobile"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    // The signing key never lives in this (public) repo: see the BUDDYPLAN_* properties in the
    // README. Without them a release build fails instead of using a throwaway debug key.
    val releaseSigning = signingConfigs.create("buddyplan").takeIf { configureBuddyplanSigning(it) }

    buildTypes {
        release {
            signingConfig = releaseSigning
        }
    }
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

gradle.taskGraph.whenReady {
    if (signingValue("BUDDYPLAN_KEYSTORE") == null && allTasks.any { it.name.startsWith("assembleRelease") || it.name.startsWith("bundleRelease") }) {
        throw GradleException(
            "Release builds need the Buddyplan signing key: set BUDDYPLAN_KEYSTORE, " +
                "BUDDYPLAN_KEYSTORE_PASSWORD, BUDDYPLAN_KEY_ALIAS and BUDDYPLAN_KEY_PASSWORD in " +
                "~/.gradle/gradle.properties (see README).",
        )
    }
}

flutter {
    source = "../.."
}
