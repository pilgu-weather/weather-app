import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")

if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.inputStream().use {
        keystoreProperties.load(it)
    }
}

fun signingProperty(name: String, envName: String): String? {
    return keystoreProperties.getProperty(name) ?: System.getenv(envName)
}

android {
    namespace = "com.kangpilgu.weatherfit"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    signingConfigs {
        create("release") {
            storeFile = file(
                signingProperty("storeFile", "WEATHERFIT_STORE_FILE")
                    ?: "../signing.keystore"
            )
            storePassword = signingProperty(
                "storePassword",
                "WEATHERFIT_STORE_PASSWORD"
            )
            keyAlias = signingProperty(
                "keyAlias",
                "WEATHERFIT_KEY_ALIAS"
            )
            keyPassword = signingProperty(
                "keyPassword",
                "WEATHERFIT_KEY_PASSWORD"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.kangpilgu.weatherfit"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

flutter {
    source = "../.."
}
