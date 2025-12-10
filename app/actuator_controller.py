"""
Actuator Controller - Manual control untuk relay/actuator
"""
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_ACTUATOR_CONTROL

def publish_actuator_command(actuator_name, state):
    """
    Publish command untuk mengontrol actuator
    
    Args:
        actuator_name (str): Nama actuator (e.g., 'pump_nutrition_AB')
        state (bool): True untuk ON, False untuk OFF
    
    Returns:
        bool: True jika berhasil publish
    """
    try:
        client = mqtt.Client(client_id="streamlit_actuator_control")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        command = {
            "actuator": actuator_name,
            "state": state,
            "source": "manual"
        }
        
        payload = json.dumps(command)
        result = client.publish(MQTT_TOPIC_ACTUATOR_CONTROL, payload)
        
        client.disconnect()
        
        return result.rc == 0
    except Exception as e:
        print(f"Error publishing actuator command: {e}")
        return False

def publish_all_actuators(actuator_states):
    """
    Publish semua status actuator sekaligus
    
    Args:
        actuator_states (dict): Dictionary dengan semua status actuator
    
    Returns:
        bool: True jika berhasil publish
    """
    try:
        client = mqtt.Client(client_id="streamlit_actuator_control_all")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        command = {
            **actuator_states,
            "source": "manual"
        }
        
        payload = json.dumps(command)
        result = client.publish(MQTT_TOPIC_ACTUATOR_CONTROL, payload)
        
        client.disconnect()
        
        return result.rc == 0
    except Exception as e:
        print(f"Error publishing all actuators: {e}")
        return False

def turn_all_off():
    """Turn off semua actuator"""
    all_off = {
        "pump_nutrition_AB": False,
        "pump_water": False,
        "pump_Ph_Up": False,
        "pump_Ph_Down": False,
        "fan": False,
        "led": False
    }
    return publish_all_actuators(all_off)

def turn_all_on():
    """Turn on semua actuator"""
    all_on = {
        "pump_nutrition_AB": True,
        "pump_water": True,
        "pump_Ph_Up": True,
        "pump_Ph_Down": True,
        "fan": True,
        "led": True
    }
    return publish_all_actuators(all_on)