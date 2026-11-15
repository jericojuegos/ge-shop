plugins {
    kotlin("jvm")
}

kotlin {
    jvmToolchain(17)
}

sourceSets {
    main {
        java.srcDirs("src/main/java", "src/main/kotlin")
    }
    test {
        java.srcDirs("src/test/java", "src/test/kotlin")
    }
}

dependencies {
    api(project(":core"))
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.9.0")
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.3")
}

tasks.test {
    useJUnitPlatform()
}

tasks.register("compileDebugKotlin") {
    dependsOn("compileKotlin")
}

tasks.register("testDebugUnitTest") {
    dependsOn("test")
}
