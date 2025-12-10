# mqtt_test_publisher.py
"""
Test MQTT Publisher - Simulates ESP32 sending data
Run this to test the dashboard without actual hardware
"""

import paho.mqtt.client as mqtt
import json
import time
import random

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_SENSOR = "part-iot/sensor/data"
TOPIC_ACTUATOR = "part-iot/actuator/status"  # NEW

def generate_sensor_data():
    """Generate random sensor data similar to real sensors"""
    return {
        "ph": round(random.uniform(5.5, 7.5), 2),
        "tds": random.randint(800, 2000),
        "water_flow": round(random.uniform(7.0, 12.0), 2),
        "air_humidity": round(random.uniform(40.0, 70.0), 2),
        "air_temperature": round(random.uniform(20.0, 28.0), 2),
        "ldr_value": random.randint(500, 3000),
        "water_temperature": round(random.uniform(22.0, 26.0), 2),
        "water_level": round(random.uniform(10.0, 15.0), 2)
    }

def generate_actuator_data():
    """Generate random actuator status"""
    return {
        "pump_nutrition_AB": random.choice([True, False]),
        "pump_water": random.choice([True, False]),
        "pump_Ph_Up": random.choice([True, False]),
        "pump_Ph_Down": random.choice([True, False]),
        "fan": random.choice([True, False]),
        "led": random.choice([True, False])
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    
    print(f"🔌 Connecting to {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    print(f"📡 Publishing sensor data to: {TOPIC_SENSOR}")
    print(f"📡 Publishing actuator status to: {TOPIC_ACTUATOR}")
    print("Press Ctrl+C to stop\n")
    
    try:
        counter = 0
        while True:
            # Publish sensor data
            sensor_data = generate_sensor_data()
            sensor_payload = json.dumps(sensor_data)
            result = client.publish(TOPIC_SENSOR, sensor_payload)
            
            if result.rc == 0:
                counter += 1
                print(f"✅ [{counter}] Sensor: pH={sensor_data['ph']}, TDS={sensor_data['tds']}, "
                      f"Temp={sensor_data['water_temperature']}°C")
            else:
                print(f"❌ Failed to publish sensor data")
            
            # Publish actuator status every 10 seconds
            if counter % 2 == 0:
                actuator_data = generate_actuator_data()
                actuator_payload = json.dumps(actuator_data)
                result = client.publish(TOPIC_ACTUATOR, actuator_payload)
                
                if result.rc == 0:
                    active_actuators = [k for k, v in actuator_data.items() if v]
                    print(f"🔧 [{counter}] Actuator: Active = {', '.join(active_actuators) if active_actuators else 'None'}")
                else:
                    print(f"❌ Failed to publish actuator data")
            
            time.sleep(5)  # Send every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping publisher...")
        client.loop_stop()
        client.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    main()