package com.example.attendance_app

import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import java.util.UUID

class BleAdvertiser(private val context: Context) {
    private val TAG = "BleAdvertiser"
    private val SERVICE_UUID = UUID.fromString("12345678-1234-1234-1234-123456789abc")
    private var advertiser: BluetoothLeAdvertiser? = null
    private var callback: AdvertiseCallback? = null

    fun startAdvertising(sessionId: String, token: String): Boolean {
        val mgr = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val adapter = mgr.adapter ?: return false
        if (!adapter.isEnabled) return false

        advertiser = adapter.bluetoothLeAdvertiser ?: return false

        val payload = "$sessionId|$token".toByteArray(Charsets.UTF_8)

        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(false)
            .setTimeout(0)
            .build()

        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(true)
            .addServiceUuid(ParcelUuid(SERVICE_UUID))
            .addManufacturerData(0x004C, payload)
            .build()

        callback = object : AdvertiseCallback() {
            override fun onStartSuccess(s: AdvertiseSettings) { Log.i(TAG, "BLE started: $sessionId | $token") }
            override fun onStartFailure(e: Int) { Log.e(TAG, "BLE failed: $e") }
        }

        advertiser?.startAdvertising(settings, data, callback)
        return true
    }

    fun stopAdvertising() {
        callback?.let { advertiser?.stopAdvertising(it) }
        callback = null
        Log.i(TAG, "BLE stopped")
    }

    fun updateToken(sessionId: String, newToken: String) {
        stopAdvertising()
        startAdvertising(sessionId, newToken)
    }
}
