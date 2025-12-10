"""
Data logging functions untuk IoT Hydroponics Dashboard
"""
import os
import json
import pandas as pd
from datetime import datetime
from config import LOG_FILE, LATEST_JSON, LATEST_ACTUATOR_JSON

def log_prediction(data, status):
    """Simpan hasil prediksi ke CSV dengan semua 4 labels"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data_row = {
            "timestamp": timestamp,
            "ph": float(data.get("ph", 0)),
            "tds": float(data.get("tds", 0)),
            "water_flow": float(data.get("water_flow", 0)),
            "air_humidity": float(data.get("air_humidity", 0)),
            "air_temperature": float(data.get("air_temperature", 0)),
            "ldr_value": float(data.get("ldr_value", 0)),
            "water_temperature": float(data.get("water_temperature", 0)),
            "water_level": float(data.get("water_level", 0)),
            "ph_label": data.get("ph_label", "Unknown"),
            "tds_label": data.get("tds_label", "Unknown"),
            "ambient_label": data.get("ambient_label", "Unknown"),
            "light_label": data.get("light_label", "Unknown"),
            "status": status
        }

        df_log = pd.DataFrame([data_row])

        if os.path.exists(LOG_FILE):
            df_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
        else:
            df_log.to_csv(LOG_FILE, mode='w', header=True, index=False)

        return True
    except Exception as e:
        print(f"Error saat logging: {e}")
        return False

def load_latest_prediction():
    """Load latest prediction dari file JSON"""
    try:
        if os.path.exists(LATEST_JSON):
            with open(LATEST_JSON, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_latest_prediction(data):
    """Save latest prediction ke file JSON"""
    try:
        with open(LATEST_JSON, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"✗ Gagal simpan latest json: {e}")
        return False

def load_log_data():
    """Load log data dari CSV"""
    try:
        if os.path.exists(LOG_FILE):
            return pd.read_csv(LOG_FILE)
    except Exception as e:
        print(f"Error loading log: {e}")
    return pd.DataFrame()

# NEW: Actuator functions
def load_latest_actuator():
    """Load latest actuator status dari file JSON"""
    try:
        if os.path.exists(LATEST_ACTUATOR_JSON):
            with open(LATEST_ACTUATOR_JSON, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_latest_actuator(data):
    """Save latest actuator status ke file JSON"""
    try:
        with open(LATEST_ACTUATOR_JSON, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"✗ Gagal simpan actuator json: {e}")
        return False