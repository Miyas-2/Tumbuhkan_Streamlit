# mqtt_test_publisher.py
"""
Test MQTT Publisher - Simulates ESP32 sending data + receiving control commands
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
TOPIC_ACTUATOR = "part-iot/actuator/status"
TOPIC_CONTROL = "part-iot/actuator/control"  # NEW: Listen for control commands

# Global actuator states
actuator_states = {
    "pump_nutrition_AB": False,
    "pump_water": False,
    "pump_Ph_Up": False,
    "pump_Ph_Down": False,
    "fan": False,
    "led": False
}

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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_CONTROL)  # Subscribe to control commands
        print(f"📡 Subscribed to control topic: {TOPIC_CONTROL}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Handle incoming control commands"""
    global actuator_states
    
    try:
        if msg.topic == TOPIC_CONTROL:
            command = json.loads(msg.payload.decode())
            print(f"\n🎮 Received control command: {command}")
            
            # Check if it's a single actuator command or batch update
            if "actuator" in command:
                # Single actuator control
                actuator = command.get("actuator")
                state = command.get("state")
                source = command.get("source", "unknown")
                
                if actuator in actuator_states:
                    actuator_states[actuator] = state
                    print(f"   → {actuator}: {'ON' if state else 'OFF'} (from {source})")
            else:
                # Batch update (all actuators)
                for key in actuator_states.keys():
                    if key in command:
                        actuator_states[key] = command[key]
                print(f"   → Batch update applied")
            
            # Immediately publish updated status
            client.publish(TOPIC_ACTUATOR, json.dumps(actuator_states))
            print(f"   ✅ Published updated actuator status\n")
            
    except Exception as e:
        print(f"❌ Error processing control command: {e}")

def main():
    global actuator_states
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"🔌 Connecting to {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    print(f"📡 Publishing sensor data to: {TOPIC_SENSOR}")
    print(f"📡 Publishing actuator status to: {TOPIC_ACTUATOR}")
    print(f"📡 Listening for control commands on: {TOPIC_CONTROL}")
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
            
            # Publish actuator status every cycle
            actuator_payload = json.dumps(actuator_states)
            result = client.publish(TOPIC_ACTUATOR, actuator_payload)
            
            if result.rc == 0:
                active_actuators = [k for k, v in actuator_states.items() if v]
                if active_actuators:
                    print(f"🔧 [{counter}] Actuators ON: {', '.join(active_actuators)}")
                else:
                    print(f"🔧 [{counter}] All actuators OFF")
            
            time.sleep(5)  # Send every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping publisher...")
        client.loop_stop()
        client.disconnect()
        print("✅ Disconnected")

if __name__ == "__main__":
    main()