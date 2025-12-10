# mqtt_config.py
"""
MQTT Configuration File for Hydroponic Dashboard
"""

# MQTT Broker Settings
MQTT_BROKER = "broker.hivemq.com"  # Public broker (change to your broker)
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sensor/data"

# Authentication (optional)
MQTT_USERNAME = ""  # Leave empty if not needed
MQTT_PASSWORD = ""  # Leave empty if not needed

# Alternative brokers you can use:
# - broker.hivemq.com (Public, no auth)
# - test.mosquitto.org (Public, no auth)
# - mqtt.eclipseprojects.io (Public, no auth)
# - Your own broker IP/domain

# Buffer settings
MAX_DATA_POINTS = 100  # Maximum historical data points to keep

# Refresh settings
DEFAULT_REFRESH_INTERVAL = 5  # seconds