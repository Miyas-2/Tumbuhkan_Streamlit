"""
IoT Hydroponics Monitoring Dashboard - FINAL VERSION
Clear control flow: Choose Manual OR Auto
"""
import json
import streamlit as st
import os
import time
import atexit
from datetime import datetime

# Import modules
from config import (MQTT_BROKER, MQTT_TOPIC_SENSOR, MQTT_TOPIC_OUTPUT, MQTT_TOPIC_ACTUATOR,
                   MQTT_TOPIC_ACTUATOR_CONTROL, LOG_FILE, FLAG_FILE, 
                   DEFAULT_LOG_INTERVAL_SECONDS)
from model_handler import load_model
from mqtt_handler import get_mqtt_client
from data_logger import load_latest_prediction, load_log_data, load_latest_actuator
from utils import get_label_color
from actuator_controller import publish_mqtt_simple, turn_all_off, turn_all_on, apply_auto_control
from visualizations import (
    create_temperature_trend_chart,
    create_ph_tds_chart,
    create_humidity_chart,
    create_light_chart,
    create_water_level_chart,
    create_status_pie_chart,
    create_label_distribution_charts,
    create_correlation_heatmap
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="IoT Hydroponics Monitoring",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CLEANUP FUNCTION
# ============================================================

def cleanup():
    """Cleanup saat aplikasi ditutup"""
    if os.path.exists(FLAG_FILE):
        try:
            os.remove(FLAG_FILE)
        except:
            pass

atexit.register(cleanup)

# ============================================================
# MAIN APP
# ============================================================

def main():
    """Main Streamlit Application"""
    
    # Header
    st.title("🌱 IoT Hydroponics Monitoring System")
    st.markdown("**Real-time Multi-Sensor Monitoring with ML Prediction & Control**")
    st.markdown("---")

    # Session State
    if 'log_interval' not in st.session_state:
        st.session_state['log_interval'] = DEFAULT_LOG_INTERVAL_SECONDS
    if 'mqtt_initialized' not in st.session_state:
        st.session_state.mqtt_initialized = False
    if 'control_mode' not in st.session_state:
        st.session_state['control_mode'] = 'Monitor Only'  # Monitor, Manual, Auto

    # Load Model
    model = load_model()

    # Setup MQTT
    if not st.session_state.mqtt_initialized:
        mqtt_client = get_mqtt_client(model, st.session_state['log_interval'])
        if mqtt_client:
            st.session_state.mqtt_initialized = True
        time.sleep(1)

    # ============================================================
    # SIDEBAR
    # ============================================================
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.info(f"**Broker:** {MQTT_BROKER}")
        st.info(f"**Topic:** {MQTT_TOPIC_ACTUATOR_CONTROL}")
        
        st.markdown("---")
        
        # Control Mode Selection
        st.subheader("🎮 Control Mode")
        control_mode = st.radio(
            "Select Control Mode:",
            options=['Monitor Only', 'Manual Control', 'Auto Control'],
            index=['Monitor Only', 'Manual Control', 'Auto Control'].index(st.session_state['control_mode'])
        )
        
        if control_mode != st.session_state['control_mode']:
            st.session_state['control_mode'] = control_mode
            st.rerun()
        
        if control_mode == 'Monitor Only':
            st.info("📊 View only - No control")
        elif control_mode == 'Manual Control':
            st.warning("🎮 Manual mode - You control actuators")
        else:
            st.success("🤖 Auto mode - ML controls actuators")
        
        st.markdown("---")
        
        if model:
            st.success("✓ Model: Loaded")
        else:
            st.warning("⚠️ Model: Not Loaded")

        if os.path.exists(FLAG_FILE):
            st.success(f"✓ MQTT: Running")
        else:
            st.error("⚠️ MQTT: Not Running")
        
        st.markdown("---")
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.rerun()

    # ============================================================
    # MAIN CONTENT
    # ============================================================

    # Load latest data
    data = load_latest_prediction()
    df_log = load_log_data()
    actuator_data = load_latest_actuator()

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs([
        "📊 Real-time Monitor", 
        "🎮 Actuator Control",
        "📈 Data & Analysis"
    ])

    # ============================================================
    # TAB 1: REAL-TIME MONITOR
    # ============================================================
    
    with tab1:
        if data:
            # Status Banner
            status = data.get('status', '—')
            icon = data.get('icon', '')
            
            if status == 'Critical':
                st.error(f"{icon} **System Status: {status}**")
            elif status == 'Optimal':
                st.success(f"{icon} **System Status: {status}**")
            else:
                st.warning(f"{icon} **System Status: {status}**")

            st.caption(f"Last Update: {data.get('timestamp', '—')}")
            st.markdown("---")

            # Sensor Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌡️ Air Temp", f"{data.get('air_temperature', '—')}°C")
                st.metric("💧 Water Temp", f"{data.get('water_temperature', '—')}°C")
            
            with col2:
                st.metric("💨 Humidity", f"{data.get('air_humidity', '—')}%")
                st.metric("📏 Water Level", f"{data.get('water_level', '—')} cm")
            
            with col3:
                st.metric("⚗️ pH", f"{data.get('ph', '—')}")
                st.metric("🧪 TDS", f"{data.get('tds', '—')} ppm")
            
            with col4:
                st.metric("💡 Light", f"{data.get('ldr_value', '—')}")
                st.metric("🌊 Flow", f"{data.get('water_flow', '—')}")

            st.markdown("---")

            # ML Predictions
            st.subheader("🤖 ML Prediction Results")
            
            pred_col1, pred_col2, pred_col3, pred_col4 = st.columns(4)
            
            with pred_col1:
                ph_label = data.get('ph_label', '—')
                st.markdown(f"**⚗️ pH:** :{get_label_color(ph_label)}[{ph_label}]")
            
            with pred_col2:
                tds_label = data.get('tds_label', '—')
                st.markdown(f"**🧪 TDS:** :{get_label_color(tds_label)}[{tds_label}]")
            
            with pred_col3:
                ambient_label = data.get('ambient_label', '—')
                st.markdown(f"**🌡️ Ambient:** :{get_label_color(ambient_label)}[{ambient_label}]")
            
            with pred_col4:
                light_label = data.get('light_label', '—')
                st.markdown(f"**💡 Light:** :{get_label_color(light_label)}[{light_label}]")

            st.markdown("---")

            # Actuator Status
            st.subheader("🔧 Actuator Status")
            
            if actuator_data:
                st.caption(f"Last Update: {actuator_data.get('timestamp', '—')}")
                
                act_col1, act_col2, act_col3, act_col4, act_col5, act_col6 = st.columns(6)
                
                with act_col1:
                    if actuator_data.get('pump_nutrition_AB'):
                        st.success("🧪 Nut ✅")
                    else:
                        st.info("🧪 Nut ⭕")
                
                with act_col2:
                    if actuator_data.get('pump_water'):
                        st.success("💧 Water ✅")
                    else:
                        st.info("💧 Water ⭕")
                
                with act_col3:
                    if actuator_data.get('pump_Ph_Up'):
                        st.success("⬆️ pH+ ✅")
                    else:
                        st.info("⬆️ pH+ ⭕")
                
                with act_col4:
                    if actuator_data.get('pump_Ph_Down'):
                        st.success("⬇️ pH- ✅")
                    else:
                        st.info("⬇️ pH- ⭕")
                
                with act_col5:
                    if actuator_data.get('fan'):
                        st.success("🌀 Fan ✅")
                    else:
                        st.info("🌀 Fan ⭕")
                
                with act_col6:
                    if actuator_data.get('led'):
                        st.success("💡 LED ✅")
                    else:
                        st.info("💡 LED ⭕")
            else:
                st.info("⏳ Waiting for actuator data...")

        else:
            st.info("⏳ Waiting for sensor data...")

    # ============================================================
    # TAB 2: ACTUATOR CONTROL (Manual OR Auto based on mode)
    # ============================================================
    
    with tab2:
        
        # Show current mode
        if st.session_state['control_mode'] == 'Monitor Only':
            st.info("📊 **Monitor Only Mode**")
            st.warning("Control is disabled. Change mode in sidebar to control actuators.")
            
            # Show current status only
            if actuator_data:
                st.subheader("🔧 Current Actuator Status")
                st.json({
                    "pump_nutrition_AB": actuator_data.get('pump_nutrition_AB', False),
                    "pump_water": actuator_data.get('pump_water', False),
                    "pump_Ph_Up": actuator_data.get('pump_Ph_Up', False),
                    "pump_Ph_Down": actuator_data.get('pump_Ph_Down', False),
                    "fan": actuator_data.get('fan', False),
                    "led": actuator_data.get('led', False)
                })
        
        elif st.session_state['control_mode'] == 'Manual Control':
            st.subheader("🎮 MANUAL ACTUATOR CONTROL")
            st.warning("⚠️ Set actuator states below, then click APPLY to send command")
            
            # Current Status
            if actuator_data:
                st.info(f"📊 Current: Nut={'ON' if actuator_data.get('pump_nutrition_AB') else 'OFF'} | "
                       f"Water={'ON' if actuator_data.get('pump_water') else 'OFF'} | "
                       f"pH+={'ON' if actuator_data.get('pump_Ph_Up') else 'OFF'} | "
                       f"pH-={'ON' if actuator_data.get('pump_Ph_Down') else 'OFF'} | "
                       f"Fan={'ON' if actuator_data.get('fan') else 'OFF'} | "
                       f"LED={'ON' if actuator_data.get('led') else 'OFF'}")
            
            st.markdown("---")
            
            # FORM
            with st.form("manual_control_form"):
                st.markdown("### Set Actuator States")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💧 Pumps:**")
                    nut = st.checkbox("🧪 Nutrition Pump A+B", value=False)
                    water = st.checkbox("💧 Water Pump", value=False)
                    ph_up = st.checkbox("⬆️ pH Up Pump", value=False)
                    ph_down = st.checkbox("⬇️ pH Down Pump", value=False)
                
                with col2:
                    st.markdown("**⚡ Utilities:**")
                    fan = st.checkbox("🌀 Cooling Fan", value=False)
                    led = st.checkbox("💡 Grow Light LED", value=False)
                
                st.markdown("---")
                
                # Submit buttons
                subcol1, subcol2, subcol3 = st.columns(3)
                
                with subcol1:
                    submit = st.form_submit_button("✅ APPLY SETTINGS", type="primary", use_container_width=True)
                with subcol2:
                    all_on = st.form_submit_button("🟢 ALL ON", use_container_width=True)
                with subcol3:
                    all_off = st.form_submit_button("🔴 ALL OFF", use_container_width=True)
                
                # Handle submission
                if submit:
                    payload = {
                        "pump_nutrition_AB": nut,
                        "pump_water": water,
                        "pump_Ph_Up": ph_up,
                        "pump_Ph_Down": ph_down,
                        "fan": fan,
                        "led": led
                    }
                    
                    st.info(f"📤 Sending command...")
                    
                    if publish_mqtt_simple(payload):
                        st.success("✅ Command sent successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to send command!")
                
                if all_on:
                    if turn_all_on():
                        st.success("✅ All actuators turned ON!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed!")
                
                if all_off:
                    if turn_all_off():
                        st.success("✅ All actuators turned OFF!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed!")
        
        else:  # Auto Control Mode
            st.subheader("🤖 AUTO CONTROL MODE")
            st.success("✅ Auto control is ACTIVE - Running automatically every 5 seconds")
            
            # Initialize last auto control time
            if 'last_auto_control' not in st.session_state:
                st.session_state.last_auto_control = 0
            
            if data:
                # Show current prediction
                st.markdown("### 📊 Current ML Prediction:")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    ph_label = data.get('ph_label', '—')
                    st.metric("⚗️ pH", ph_label)
                with col2:
                    tds_label = data.get('tds_label', '—')
                    st.metric("🧪 TDS", tds_label)
                with col3:
                    ambient_label = data.get('ambient_label', '—')
                    st.metric("🌡️ Ambient", ambient_label)
                with col4:
                    light_label = data.get('light_label', '—')
                    st.metric("💡 Light", light_label)
                
                st.markdown("---")
                
                # Calculate what will happen
                st.markdown("### 🎯 Auto Control Status:")
                
                # Simple auto logic inline
                predicted = {
                    "pump_nutrition_AB": tds_label in ['Too Low', 'Low'],
                    "pump_water": tds_label in ['Too High', 'High'],
                    "pump_Ph_Up": ph_label in ['Too Low', 'Low'],
                    "pump_Ph_Down": ph_label in ['Too High', 'High'],
                    "fan": ambient_label in ['Bad', 'Slightly Off'],
                    "led": light_label == 'Too Dark'
                }
                
                # Show current auto control state
                pred_col1, pred_col2, pred_col3 = st.columns(3)
                
                with pred_col1:
                    st.markdown(f"**🧪 Nutrition:** {'✅ ON' if predicted['pump_nutrition_AB'] else '⭕ OFF'}")
                    st.markdown(f"**💧 Water:** {'✅ ON' if predicted['pump_water'] else '⭕ OFF'}")
                
                with pred_col2:
                    st.markdown(f"**⬆️ pH Up:** {'✅ ON' if predicted['pump_Ph_Up'] else '⭕ OFF'}")
                    st.markdown(f"**⬇️ pH Down:** {'✅ ON' if predicted['pump_Ph_Down'] else '⭕ OFF'}")
                
                with pred_col3:
                    st.markdown(f"**🌀 Fan:** {'✅ ON' if predicted['fan'] else '⭕ OFF'}")
                    st.markdown(f"**💡 LED:** {'✅ ON' if predicted['led'] else '⭕ OFF'}")
                
                st.markdown("---")
                
                # AUTO APPLY LOGIC - Every 5 seconds
                current_time = time.time()
                time_since_last = current_time - st.session_state.last_auto_control
                
                if time_since_last >= 5:  # Apply every 5 seconds
                    st.info("🤖 Applying auto control...")
                    
                    # Direct publish predicted states
                    if publish_mqtt_simple(predicted):
                        st.session_state.last_auto_control = current_time
                        st.success(f"✅ Auto control applied at {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        st.error("❌ Auto control failed!")
                else:
                    next_apply = 5 - int(time_since_last)
                    st.info(f"⏳ Next auto control in {next_apply} seconds...")
                
                # Show logic
                with st.expander("🧠 Auto Control Logic", expanded=False):
                    logic_col1, logic_col2 = st.columns(2)
                    
                    with logic_col1:
                        st.markdown("**pH Control:**")
                        st.markdown("- Too Low / Low → pH Up ON")
                        st.markdown("- Too High / High → pH Down ON")
                        st.markdown("")
                        st.markdown("**TDS Control:**")
                        st.markdown("- Too Low / Low → Nutrition ON")
                        st.markdown("- Too High / High → Water ON")
                    
                    with logic_col2:
                        st.markdown("**Ambient Control:**")
                        st.markdown("- Bad / Slightly Off → Fan ON")
                        st.markdown("")
                        st.markdown("**Light Control:**")
                        st.markdown("- Too Dark → LED ON")
                
                # Manual override option
                st.markdown("---")
                st.markdown("### ⚡ Manual Override")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 APPLY NOW (Manual Trigger)", use_container_width=True, type="secondary"):
                        if publish_mqtt_simple(predicted):
                            st.session_state.last_auto_control = time.time()
                            st.success("✅ Manual override applied!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed!")
                
                with col2:
                    if st.button("⏸️ Switch to Manual Mode", use_container_width=True):
                        st.session_state['control_mode'] = 'Manual Control'
                        st.rerun()
            
            else:
                st.warning("⏳ Waiting for sensor data...")
                st.info("Auto control needs ML prediction data to work")
    # ============================================================
    # TAB 3: DATA & ANALYSIS
    # ============================================================
    
    with tab3:
        if not df_log.empty:
            st.subheader("📈 Sensor Data Trends")
            
            # Temperature Trends
            temp_chart = create_temperature_trend_chart(df_log)
            if temp_chart:
                st.plotly_chart(temp_chart, use_container_width=True)

            col1, col2 = st.columns(2)
            
            with col1:
                ph_tds_chart = create_ph_tds_chart(df_log)
                if ph_tds_chart:
                    st.plotly_chart(ph_tds_chart, use_container_width=True)
            
            with col2:
                water_chart = create_water_level_chart(df_log)
                if water_chart:
                    st.plotly_chart(water_chart, use_container_width=True)

            st.markdown("---")

            # Data Log
            st.subheader("📋 Data Log")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.download_button(
                    label="📥 Download CSV",
                    data=df_log.to_csv(index=False),
                    file_name=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            display_df = df_log.tail(50).sort_values('timestamp', ascending=False)
            st.dataframe(display_df, hide_index=True, use_container_width=True, height=400)

        else:
            st.info("📝 No data available yet")

    # ============================================================
    # FOOTER
    # ============================================================
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("💡 ESP32 → MQTT → ML → Control")
    with col2:
        st.caption(f"Mode: **{st.session_state['control_mode']}**")
    with col3:
        st.caption("Auto-refresh: 3s")

    # Auto-refresh
    time.sleep(3)
    st.rerun()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()