import org.w3c.dom.Element
import javax.xml.parsers.DocumentBuilderFactory

plugins {
    kotlin("jvm") version "2.0.21" apply false
}

abstract class CheckMergedManifestPermissions : DefaultTask() {
    @get:InputFiles
    abstract val manifestFiles: ListProperty<RegularFile>

    @get:Input
    abstract val allowedPermissions: SetProperty<String>

    @get:Input
    abstract val prohibitedPermissions: SetProperty<String>

    @TaskAction
    fun checkManifests() {
        val allowed = allowedPermissions.get()
        val prohibited = prohibitedPermissions.get()

        for (file in manifestFiles.get()) {
            val manifestFile = file.asFile
            if (!manifestFile.exists()) continue

            val doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(manifestFile)
            val permissionNodes = doc.getElementsByTagName("uses-permission")

            for (i in 0 until permissionNodes.length) {
                val element = permissionNodes.item(i) as Element
                val permissionName = element.getAttribute("android:name")

                if (prohibited.contains(permissionName)) {
                    throw GradleException("FATAL: Merged manifest '${manifestFile.name}' contains prohibited permission: $permissionName")
                }
                if (!allowed.contains(permissionName)) {
                    throw GradleException("FATAL: Merged manifest '${manifestFile.name}' contains unapproved permission: $permissionName. Allowed: $allowed")
                }
            }
        }
        logger.lifecycle("Merged manifest permissions verified against allowlist.")
    }
}

tasks.register<CheckMergedManifestPermissions>("checkMergedManifestPermissions") {
    manifestFiles.set(listOf(layout.projectDirectory.file("app/src/main/AndroidManifest.xml")))
    allowedPermissions.set(setOf("android.permission.INTERNET"))
    prohibitedPermissions.set(
        setOf(
            "android.permission.READ_CONTACTS",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.RECORD_AUDIO",
        )
    )
}

tasks.register("compileDebugKotlin") {
    dependsOn(":core:compileKotlin", ":app:compileKotlin")
}

tasks.register("testDebugUnitTest") {
    dependsOn(":core:test", ":app:test")
}
