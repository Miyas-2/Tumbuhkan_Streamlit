"""
Actuator Controller - SUPER SIMPLE VERSION
No complex logic, just simple publish
"""
import json
import paho.mqtt.client as mqtt
import time

# Import config
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_ACTUATOR_CONTROL

def publish_mqtt_simple(payload_dict):
    """
    Simple MQTT publish - PALING BASIC
    
    Args:
        payload_dict (dict): Dictionary dengan 6 actuator
    
    Returns:
        bool: True jika berhasil
    """
    try:
        # Create client ID unik
        client_id = f"streamlit_{int(time.time()*1000)}"
        
        print(f"\n{'='*60}")
        print(f"📤 MQTT PUBLISH")
        print(f"{'='*60}")
        print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Topic: {MQTT_TOPIC_ACTUATOR_CONTROL}")
        print(f"Client ID: {client_id}")
        
        # Create client (simple, no callback version)
        try:
            # Try new version
            client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id
            )
        except:
            # Fallback old version
            client = mqtt.Client(client_id=client_id)
        
        # Connect
        print(f"🔌 Connecting...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        client.loop_start()
        time.sleep(1)  # Wait 1 detik untuk koneksi stabil
        
        # Convert to JSON
        payload_json = json.dumps(payload_dict)
        print(f"📦 Payload:")
        print(f"   {payload_json}")
        
        # Publish
        print(f"📡 Publishing...")
        info = client.publish(MQTT_TOPIC_ACTUATOR_CONTROL, payload_json, qos=0)
        
        # Wait for publish
        info.wait_for_publish()
        
        # Check result
        if info.is_published():
            print(f"✅ SUCCESS - Message published!")
            success = True
        else:
            print(f"❌ FAILED - Message not published (RC: {info.rc})")
            success = False
        
        # Cleanup
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        
        print(f"{'='*60}\n")
        
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def publish_actuator_command(actuator_name, state):
    """
    Publish single actuator command
    SIMPLE: Load from file, update one, send all
    """
    import os
    from config import LATEST_ACTUATOR_JSON
    
    # Default payload
    payload = {
        "pump_nutrition_AB": False,
        "pump_water": False,
        "pump_Ph_Up": False,
        "pump_Ph_Down": False,
        "fan": False,
        "led": False
    }
    
    # Try load from file
    try:
        if os.path.exists(LATEST_ACTUATOR_JSON):
            with open(LATEST_ACTUATOR_JSON, 'r') as f:
                data = json.load(f)
                # Update payload dengan data dari file (tanpa timestamp)
                for key in payload.keys():
                    if key in data:
                        payload[key] = data[key]
    except:
        pass  # Use default if fail
    
    # Update yang diubah
    payload[actuator_name] = state
    
    print(f"\n🎮 CONTROL: {actuator_name} = {state}")
    
    # Publish
    return publish_mqtt_simple(payload)

def publish_all_actuators(actuator_states):
    """
    Publish all actuators
    SIMPLE: Just send the dict directly
    """
    return publish_mqtt_simple(actuator_states)

def turn_all_on():
    """Turn all ON"""
    payload = {
        "pump_nutrition_AB": True,
        "pump_water": True,
        "pump_Ph_Up": True,
        "pump_Ph_Down": True,
        "fan": True,
        "led": True
    }
    print("🟢 TURN ALL ON")
    return publish_mqtt_simple(payload)

def turn_all_off():
    """Turn all OFF"""
    payload = {
        "pump_nutrition_AB": False,
        "pump_water": False,
        "pump_Ph_Up": False,
        "pump_Ph_Down": False,
        "fan": False,
        "led": False
    }
    print("🔴 TURN ALL OFF")
    return publish_mqtt_simple(payload)

# ============================================================
# AUTO CONTROL - SIMPLIFIED
# ============================================================

def apply_auto_control(prediction_result):
    """
    Auto control based on ML prediction - SIMPLE VERSION
    """
    from config import PH_LABELS, TDS_LABELS, AMBIENT_LABELS, LIGHT_LABELS
    
    # Get labels
    ph_label = prediction_result.get('ph_label', 'Normal')
    tds_label = prediction_result.get('tds_label', 'Normal')
    ambient_label = prediction_result.get('ambient_label', 'Ideal')
    light_label = prediction_result.get('light_label', 'Normal')
    
    print(f"\n🤖 AUTO CONTROL LOGIC:")
    print(f"   pH: {ph_label}")
    print(f"   TDS: {tds_label}")
    print(f"   Ambient: {ambient_label}")
    print(f"   Light: {light_label}")
    
    # Initialize all OFF
    payload = {
        "pump_nutrition_AB": False,
        "pump_water": False,
        "pump_Ph_Up": False,
        "pump_Ph_Down": False,
        "fan": False,
        "led": False
    }
    
    # pH Control Logic
    if ph_label == "Too Low":
        payload["pump_Ph_Up"] = True
        print(f"   → pH Up ON (pH too low)")
    elif ph_label == "Low":
        payload["pump_Ph_Up"] = True
        print(f"   → pH Up ON (pH low)")
    elif ph_label == "Too High":
        payload["pump_Ph_Down"] = True
        print(f"   → pH Down ON (pH too high)")
    elif ph_label == "High":
        payload["pump_Ph_Down"] = True
        print(f"   → pH Down ON (pH high)")
    
    # TDS Control Logic
    if tds_label == "Too Low":
        payload["pump_nutrition_AB"] = True
        print(f"   → Nutrition ON (TDS too low)")
    elif tds_label == "Low":
        payload["pump_nutrition_AB"] = True
        print(f"   → Nutrition ON (TDS low)")
    elif tds_label == "Too High":
        payload["pump_water"] = True
        print(f"   → Water Pump ON (TDS too high)")
    elif tds_label == "High":
        payload["pump_water"] = True
        print(f"   → Water Pump ON (TDS high)")
    
    # Ambient Control Logic
    if ambient_label == "Bad":
        payload["fan"] = True
        print(f"   → Fan ON (ambient bad)")
    elif ambient_label == "Slightly Off":
        payload["fan"] = True
        print(f"   → Fan ON (ambient slightly off)")
    
    # Light Control Logic
    if light_label == "Too Dark":
        payload["led"] = True
        print(f"   → LED ON (too dark)")
    
    # Publish
    print(f"\n   Final command: {payload}")
    return publish_mqtt_simple(payload)

# ============================================================
# TEST FUNCTION
# ============================================================

def test():
    """Simple test"""
    print("\n" + "="*70)
    print(" "*20 + "🧪 ACTUATOR TEST")
    print("="*70)
    
    # Test 1: Turn all OFF
    print("\n[TEST 1] Turn all OFF")
    result1 = turn_all_off()
    time.sleep(2)
    
    # Test 2: Turn FAN ON only
    print("\n[TEST 2] Turn FAN ON only")
    result2 = publish_actuator_command('fan', True)
    time.sleep(2)
    
    # Test 3: Turn LED ON (FAN should stay ON)
    print("\n[TEST 3] Turn LED ON (FAN should stay ON)")
    result3 = publish_actuator_command('led', True)
    time.sleep(2)
    
    # Test 4: Turn all OFF again
    print("\n[TEST 4] Turn all OFF")
    result4 = turn_all_off()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS:")
    print(f"   Test 1 (All OFF): {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"   Test 2 (FAN ON): {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"   Test 3 (LED ON): {'✅ PASS' if result3 else '❌ FAIL'}")
    print(f"   Test 4 (All OFF): {'✅ PASS' if result4 else '❌ FAIL'}")
    print("="*70 + "\n")
    
    return all([result1, result2, result3, result4])

if __name__ == "__main__":
    test()