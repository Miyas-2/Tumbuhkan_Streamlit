"""
MQTT handling untuk IoT Hydroponics Dashboard
"""
import os
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
from config import (MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_SENSOR, MQTT_TOPIC_OUTPUT, 
                   MQTT_TOPIC_ACTUATOR, DEFAULT_LOG_INTERVAL_SECONDS, FLAG_FILE)
from model_handler import predict_condition
from data_logger import log_prediction, save_latest_prediction, save_latest_actuator
from utils import safe_float

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback saat koneksi berhasil"""
    if rc == 0:
        print(f"✓ Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC_SENSOR)
        client.subscribe(MQTT_TOPIC_ACTUATOR)  # NEW: Subscribe to actuator topic
        print(f"📡 Subscribed to: {MQTT_TOPIC_SENSOR}")
        print(f"📡 Subscribed to: {MQTT_TOPIC_ACTUATOR}")
    else:
        print(f"✗ Connection failed: {rc}")

def on_message(client, userdata, msg):
    """Callback saat terima message"""
    try:
        # NEW: Handle actuator status messages
        if msg.topic == MQTT_TOPIC_ACTUATOR:
            actuator_data = json.loads(msg.payload.decode())
            actuator_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_latest_actuator(actuator_data)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔧 Actuator Status Updated")
            return

        # Handle sensor data messages
        payload = json.loads(msg.payload.decode())

        # Ambil semua sensor dari payload
        ph = safe_float(payload.get("ph", 0))
        tds = safe_float(payload.get("tds", 0))
        water_flow = safe_float(payload.get("water_flow", 0))
        air_humidity = safe_float(payload.get("air_humidity", 0))
        air_temperature = safe_float(payload.get("air_temperature", 0))
        ldr = safe_float(payload.get("ldr_value", 0))
        water_temperature = safe_float(payload.get("water_temperature", 0))
        water_level = safe_float(payload.get("water_level", 0))

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 pH: {ph} | TDS: {tds} | WaterT: {water_temperature}°C | AirT: {air_temperature}°C | Hum: {air_humidity}% | LDR: {ldr}")

        # Ambil model dari userdata
        model = userdata.get('model') if isinstance(userdata, dict) else None

        # Prediksi
        prediction_result = predict_condition(payload, model)
        
        # Extract labels
        ph_label = prediction_result.get('ph_label', 'Unknown')
        tds_label = prediction_result.get('tds_label', 'Unknown')
        ambient_label = prediction_result.get('ambient_label', 'Unknown')
        light_label = prediction_result.get('light_label', 'Unknown')
        
        # Tentukan status keseluruhan
        critical_ph = ph_label in ['Too Low', 'Too High']
        critical_tds = tds_label in ['Too Low', 'Too High']
        critical_ambient = ambient_label == 'Bad'
        
        if critical_ph or critical_tds or critical_ambient:
            output = "ALERT_CRITICAL"
            icon = "🚨"
            color = "red"
            status = "Critical"
        elif ph_label == 'Normal' and tds_label == 'Normal' and ambient_label == 'Ideal' and light_label == 'Normal':
            output = "ALL_NORMAL"
            icon = "✅"
            color = "green"
            status = "Optimal"
        else:
            output = "NEEDS_ATTENTION"
            icon = "⚠️"
            color = "orange"
            status = "Warning"

        # Publish output
        try:
            output_data = {
                "status": status,
                "ph": ph_label,
                "tds": tds_label,
                "ambient": ambient_label,
                "light": light_label,
                "action": output
            }
            client.publish(MQTT_TOPIC_OUTPUT, json.dumps(output_data))
        except Exception as e:
            print(f"✗ Gagal publish output: {e}")

        # Logging dengan interval
        current_time = time.time()
        log_interval = userdata.get('log_interval', DEFAULT_LOG_INTERVAL_SECONDS) if isinstance(userdata, dict) else DEFAULT_LOG_INTERVAL_SECONDS
        last_logged_time = userdata.get('last_logged_time', 0) if isinstance(userdata, dict) else 0
        should_log = (current_time - last_logged_time) >= log_interval

        if should_log:
            logged = log_prediction({
                "ph": ph,
                "tds": tds,
                "water_flow": water_flow,
                "air_humidity": air_humidity,
                "air_temperature": air_temperature,
                "ldr_value": ldr,
                "water_temperature": water_temperature,
                "water_level": water_level,
                "ph_label": ph_label,
                "tds_label": tds_label,
                "ambient_label": ambient_label,
                "light_label": light_label
            }, status)

            if isinstance(userdata, dict):
                userdata['last_logged_time'] = current_time
                client.user_data_set(userdata)

            if logged:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 LOGGED → {ph_label} | {tds_label} | {ambient_label} | {light_label}")

        # Simpan latest_prediction.json
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ph": ph,
            "tds": tds,
            "water_flow": water_flow,
            "air_humidity": air_humidity,
            "air_temperature": air_temperature,
            "ldr_value": ldr,
            "water_temperature": water_temperature,
            "water_level": water_level,
            "ph_label": ph_label,
            "tds_label": tds_label,
            "ambient_label": ambient_label,
            "light_label": light_label,
            "status": status,
            "output": output,
            "icon": icon,
            "color": color
        }
        save_latest_prediction(data)

    except Exception as e:
        print(f"✗ Error on_message: {e}")

def on_disconnect(client, userdata, rc, properties=None):
    """Callback saat disconnect"""
    if rc != 0:
        print(f"⚠️ Disconnected: {rc}")

def get_mqtt_client(model, log_interval):
    """Get atau create MQTT client"""
    if os.path.exists(FLAG_FILE):
        return None

    print("🔌 Creating new MQTT client...")

    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"streamlit_iot_{int(time.time())}"
        )
    except Exception:
        client = mqtt.Client(client_id=f"streamlit_iot_{int(time.time())}")

    userdata = {
        'model': model,
        'log_interval': log_interval,
        'last_logged_time': 0
    }
    client.user_data_set(userdata)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        with open(FLAG_FILE, 'w') as f:
            f.write(str(os.getpid()))

        print(f"✓ MQTT client connected with Log Interval: {log_interval}s")
        return client

    except Exception as e:
        print(f"✗ Failed connect MQTT: {e}")
        return None