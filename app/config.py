"""
Configuration file untuk IoT Hydroponics Dashboard
"""

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "part-iot/sensor/data"
MQTT_TOPIC_OUTPUT = "part-iot/output"
MQTT_TOPIC_ACTUATOR = "part-iot/actuator/status"
MQTT_TOPIC_ACTUATOR_CONTROL = "part-iot/actuator/control"  # NEW: Topic untuk kontrol manual

# File Paths
MODEL_PATH = "../model/hydroponic_multioutput_rf_model.pkl"
LOG_FILE = "prediction_log.csv"
LATEST_JSON = "latest_prediction.json"
LATEST_ACTUATOR_JSON = "latest_actuator.json"
FLAG_FILE = "mqtt_running.flag"

# Logging Configuration
DEFAULT_LOG_INTERVAL_SECONDS = 5

# Label Mappings
PH_LABELS = {0: 'Too Low', 1: 'Low', 2: 'Normal', 3: 'High', 4: 'Too High'}
TDS_LABELS = {0: 'Too Low', 1: 'Low', 2: 'Normal', 3: 'High', 4: 'Too High'}
AMBIENT_LABELS = {0: 'Bad', 1: 'Slightly Off', 2: 'Ideal'}
LIGHT_LABELS = {0: 'Too Dark', 1: 'Normal', 2: 'Too Bright'}

# Color Mappings
STATUS_COLORS = {
    'Critical': '#ff4444',
    'Optimal': '#44ff44',
    'Warning': '#ff9944'
}

LABEL_COLORS = {
    'Normal': 'green',
    'Low': 'orange',
    'High': 'orange',
    'Too Low': 'red',
    'Too High': 'red',
    'Ideal': 'green',
    'Slightly Off': 'orange',
    'Bad': 'red',
    'Too Dark': 'orange',
    'Too Bright': 'orange'
}

# Actuator Configuration
ACTUATOR_NAMES = {
    'pump_nutrition_AB': '🧪 Nutrition Pump A+B',
    'pump_water': '💧 Water Pump',
    'pump_Ph_Up': '⬆️ pH Up Pump',
    'pump_Ph_Down': '⬇️ pH Down Pump',
    'fan': '🌀 Cooling Fan',
    'led': '💡 Grow Light LED'
}

ACTUATOR_KEYS = [
    'pump_nutrition_AB',
    'pump_water', 
    'pump_Ph_Up',
    'pump_Ph_Down',
    'fan',
    'led'
]