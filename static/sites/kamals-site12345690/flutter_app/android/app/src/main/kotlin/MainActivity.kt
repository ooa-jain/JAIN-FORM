package com.example.attendance_app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.attendance/ble"
    private lateinit var ble: BleAdvertiser

    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)
        ble = BleAdvertiser(this)

        MethodChannel(engine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "startAdvertising" -> {
                    val ok = ble.startAdvertising(
                        call.argument<String>("sessionId") ?: "",
                        call.argument<String>("token") ?: ""
                    )
                    result.success(ok)
                }
                "stopAdvertising" -> { ble.stopAdvertising(); result.success(true) }
                "updateToken" -> {
                    ble.updateToken(
                        call.argument<String>("sessionId") ?: "",
                        call.argument<String>("token") ?: ""
                    )
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }
}
