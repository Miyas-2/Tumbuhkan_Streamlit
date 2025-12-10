"""
IoT Hydroponics Monitoring Dashboard - Main Application
Modular version with comprehensive visualizations + Manual Actuator Control
"""
import streamlit as st
import os
import time
import atexit
from datetime import datetime

# Import modules
from config import (MQTT_BROKER, MQTT_TOPIC_SENSOR, MQTT_TOPIC_OUTPUT, MQTT_TOPIC_ACTUATOR,
                   MQTT_TOPIC_ACTUATOR_CONTROL, LOG_FILE, FLAG_FILE, 
                   DEFAULT_LOG_INTERVAL_SECONDS, ACTUATOR_NAMES, ACTUATOR_KEYS)
from model_handler import load_model
from mqtt_handler import get_mqtt_client
from data_logger import load_latest_prediction, load_log_data, load_latest_actuator
from utils import get_label_color
from actuator_controller import publish_actuator_command, turn_all_off, turn_all_on
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
            print("🧹 Cleanup: MQTT flag removed")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")

atexit.register(cleanup)

# ============================================================
# MAIN APP
# ============================================================

def main():
    """Main Streamlit Application"""
    
    # Header
    st.title("🌱 IoT Hydroponics Monitoring System")
    st.markdown("**Real-time Multi-Sensor Monitoring with ML Prediction & Manual Control**")
    st.markdown("---")

    # Session State
    if 'log_interval' not in st.session_state:
        st.session_state['log_interval'] = DEFAULT_LOG_INTERVAL_SECONDS
    if 'mqtt_initialized' not in st.session_state:
        st.session_state.mqtt_initialized = False
    
    # NEW: Session state untuk actuator control
    if 'manual_mode' not in st.session_state:
        st.session_state['manual_mode'] = False
    
    for actuator in ACTUATOR_KEYS:
        if f'actuator_{actuator}' not in st.session_state:
            st.session_state[f'actuator_{actuator}'] = False

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
        
        with st.expander("📡 MQTT Settings", expanded=True):
            st.info(f"**Broker:** {MQTT_BROKER}")
            st.info(f"**Sensor:** {MQTT_TOPIC_SENSOR}")
            st.info(f"**Output:** {MQTT_TOPIC_OUTPUT}")
            st.info(f"**Actuator:** {MQTT_TOPIC_ACTUATOR}")
            st.info(f"**Control:** {MQTT_TOPIC_ACTUATOR_CONTROL}")

        with st.expander("💾 Log Settings"):
            new_interval = st.number_input(
                "Log Interval (seconds)",
                min_value=1,
                max_value=3600,
                value=st.session_state['log_interval'],
                step=1
            )
            st.session_state['log_interval'] = new_interval

            if st.button("🔄 Apply & Restart MQTT"):
                if os.path.exists(FLAG_FILE):
                    try:
                        os.remove(FLAG_FILE)
                    except:
                        pass
                st.session_state.mqtt_initialized = False
                st.rerun()

        st.markdown("---")
        st.subheader("📊 System Status")

        if model:
            st.success("✓ Model: Loaded")
        else:
            st.warning("⚠️ Model: Not Loaded")

        if os.path.exists(FLAG_FILE):
            st.success(f"✓ MQTT: Running")
            st.caption(f"Log interval: {st.session_state['log_interval']}s")
        else:
            st.error("⚠️ MQTT: Not Running")
            if st.button("🔄 Start MQTT"):
                st.session_state.mqtt_initialized = False
                st.rerun()

        st.markdown("---")
        
        # NEW: Manual Control Toggle
        st.subheader("🎮 Control Mode")
        manual_mode = st.toggle("Enable Manual Control", value=st.session_state['manual_mode'])
        st.session_state['manual_mode'] = manual_mode
        
        if manual_mode:
            st.warning("⚠️ Manual control is active")
            st.caption("You can control actuators manually")
        else:
            st.info("🤖 Auto mode (ML controlled)")
        
        st.markdown("---")
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()

    # ============================================================
    # MAIN CONTENT
    # ============================================================

    # Load latest data
    data = load_latest_prediction()
    df_log = load_log_data()
    actuator_data = load_latest_actuator()

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Real-time Monitor", 
        "🎮 Manual Control",  # NEW TAB
        "📈 Sensor Trends", 
        "🎯 Analysis", 
        "📋 Data Log"
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

            # Sensor Metrics - Row 1
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌡️ Air Temperature", f"{data.get('air_temperature', '—')}°C")
                st.metric("💧 Water Temperature", f"{data.get('water_temperature', '—')}°C")
            
            with col2:
                st.metric("💨 Air Humidity", f"{data.get('air_humidity', '—')}%")
                st.metric("📏 Water Level", f"{data.get('water_level', '—')} cm")
            
            with col3:
                st.metric("⚗️ pH Level", f"{data.get('ph', '—')}")
                st.metric("🧪 TDS", f"{data.get('tds', '—')} ppm")
            
            with col4:
                st.metric("💡 Light (LDR)", f"{data.get('ldr_value', '—')}")
                st.metric("🌊 Water Flow", f"{data.get('water_flow', '—')}")

            st.markdown("---")

            # ML Predictions
            st.subheader("🤖 ML Prediction Results")
            
            pred_col1, pred_col2, pred_col3, pred_col4 = st.columns(4)
            
            with pred_col1:
                ph_label = data.get('ph_label', '—')
                ph_color = get_label_color(ph_label)
                st.markdown(f"**⚗️ pH Status**")
                st.markdown(f":{ph_color}[{ph_label}]")
            
            with pred_col2:
                tds_label = data.get('tds_label', '—')
                tds_color = get_label_color(tds_label)
                st.markdown(f"**🧪 TDS Status**")
                st.markdown(f":{tds_color}[{tds_label}]")
            
            with pred_col3:
                ambient_label = data.get('ambient_label', '—')
                ambient_color = get_label_color(ambient_label)
                st.markdown(f"**🌡️ Ambient Status**")
                st.markdown(f":{ambient_color}[{ambient_label}]")
            
            with pred_col4:
                light_label = data.get('light_label', '—')
                light_color = get_label_color(light_label)
                st.markdown(f"**💡 Light Status**")
                st.markdown(f":{light_color}[{light_label}]")

            # Output Command
            st.markdown("---")
            output = data.get('output', '—')
            if output == "ALERT_CRITICAL":
                st.error(f"⚡ **Action Required:** {output}")
            elif output == "ALL_NORMAL":
                st.success(f"✅ **System Response:** {output}")
            else:
                st.warning(f"⚠️ **Advisory:** {output}")

            # Actuator Status Display
            st.markdown("---")
            st.subheader("🔧 Actuator Status (Read-only)")
            
            if actuator_data:
                st.caption(f"Last Updated: {actuator_data.get('timestamp', '—')}")
                
                act_col1, act_col2, act_col3 = st.columns(3)
                
                with act_col1:
                    nutrition_status = actuator_data.get('pump_nutrition_AB', False)
                    if nutrition_status:
                        st.success(f"🧪 **Nutrition Pump A+B:** ✅ ON")
                    else:
                        st.info(f"🧪 **Nutrition Pump A+B:** ⭕ OFF")
                    
                    water_pump_status = actuator_data.get('pump_water', False)
                    if water_pump_status:
                        st.success(f"💧 **Water Pump:** ✅ ON")
                    else:
                        st.info(f"💧 **Water Pump:** ⭕ OFF")
                
                with act_col2:
                    ph_up_status = actuator_data.get('pump_Ph_Up', False)
                    if ph_up_status:
                        st.success(f"⬆️ **pH Up Pump:** ✅ ON")
                    else:
                        st.info(f"⬆️ **pH Up Pump:** ⭕ OFF")
                    
                    ph_down_status = actuator_data.get('pump_Ph_Down', False)
                    if ph_down_status:
                        st.success(f"⬇️ **pH Down Pump:** ✅ ON")
                    else:
                        st.info(f"⬇️ **pH Down Pump:** ⭕ OFF")
                
                with act_col3:
                    fan_status = actuator_data.get('fan', False)
                    if fan_status:
                        st.success(f"🌀 **Cooling Fan:** ✅ ON")
                    else:
                        st.info(f"🌀 **Cooling Fan:** ⭕ OFF")
                    
                    led_status = actuator_data.get('led', False)
                    if led_status:
                        st.success(f"💡 **Grow Light LED:** ✅ ON")
                    else:
                        st.info(f"💡 **Grow Light LED:** ⭕ OFF")
            else:
                st.info("⏳ Waiting for actuator data...")

        else:
            st.info("⏳ Waiting for sensor data...")
            st.caption("Make sure MQTT publisher is running and sending data.")

    # ============================================================
    # TAB 2: MANUAL CONTROL (NEW)
    # ============================================================
    
    with tab2:
        st.subheader("🎮 Manual Actuator Control")
        
        if not st.session_state['manual_mode']:
            st.warning("⚠️ Manual control is disabled. Enable it in the sidebar first.")
            st.info("👈 Go to sidebar and toggle 'Enable Manual Control'")
        else:
            st.success("✅ Manual control is active")
            
            # Quick Actions
            st.markdown("### ⚡ Quick Actions")
            quick_col1, quick_col2, quick_col3 = st.columns(3)
            
            with quick_col1:
                if st.button("🟢 Turn All ON", use_container_width=True, type="primary"):
                    if turn_all_on():
                        st.success("✅ All actuators turned ON")
                        for actuator in ACTUATOR_KEYS:
                            st.session_state[f'actuator_{actuator}'] = True
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to turn on actuators")
            
            with quick_col2:
                if st.button("🔴 Turn All OFF", use_container_width=True):
                    if turn_all_off():
                        st.success("✅ All actuators turned OFF")
                        for actuator in ACTUATOR_KEYS:
                            st.session_state[f'actuator_{actuator}'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to turn off actuators")
            
            with quick_col3:
                if st.button("🔄 Refresh Status", use_container_width=True):
                    st.rerun()
            
            st.markdown("---")
            
            # Individual Controls
            st.markdown("### 🎛️ Individual Control")
            
            ctrl_col1, ctrl_col2 = st.columns(2)
            
            with ctrl_col1:
                st.markdown("#### 💧 Pumps")
                
                # Nutrition Pump
                nutrition_state = st.toggle(
                    "🧪 Nutrition Pump A+B",
                    value=st.session_state['actuator_pump_nutrition_AB'],
                    key='toggle_nutrition'
                )
                if nutrition_state != st.session_state['actuator_pump_nutrition_AB']:
                    if publish_actuator_command('pump_nutrition_AB', nutrition_state):
                        st.session_state['actuator_pump_nutrition_AB'] = nutrition_state
                        st.success(f"✅ Nutrition Pump {'ON' if nutrition_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control Nutrition Pump")
                
                # Water Pump
                water_state = st.toggle(
                    "💧 Water Pump",
                    value=st.session_state['actuator_pump_water'],
                    key='toggle_water'
                )
                if water_state != st.session_state['actuator_pump_water']:
                    if publish_actuator_command('pump_water', water_state):
                        st.session_state['actuator_pump_water'] = water_state
                        st.success(f"✅ Water Pump {'ON' if water_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control Water Pump")
                
                # pH Up Pump
                ph_up_state = st.toggle(
                    "⬆️ pH Up Pump",
                    value=st.session_state['actuator_pump_Ph_Up'],
                    key='toggle_ph_up'
                )
                if ph_up_state != st.session_state['actuator_pump_Ph_Up']:
                    if publish_actuator_command('pump_Ph_Up', ph_up_state):
                        st.session_state['actuator_pump_Ph_Up'] = ph_up_state
                        st.success(f"✅ pH Up Pump {'ON' if ph_up_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control pH Up Pump")
                
                # pH Down Pump
                ph_down_state = st.toggle(
                    "⬇️ pH Down Pump",
                    value=st.session_state['actuator_pump_Ph_Down'],
                    key='toggle_ph_down'
                )
                if ph_down_state != st.session_state['actuator_pump_Ph_Down']:
                    if publish_actuator_command('pump_Ph_Down', ph_down_state):
                        st.session_state['actuator_pump_Ph_Down'] = ph_down_state
                        st.success(f"✅ pH Down Pump {'ON' if ph_down_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control pH Down Pump")
            
            with ctrl_col2:
                st.markdown("#### ⚡ Utilities")
                
                # Fan
                fan_state = st.toggle(
                    "🌀 Cooling Fan",
                    value=st.session_state['actuator_fan'],
                    key='toggle_fan'
                )
                if fan_state != st.session_state['actuator_fan']:
                    if publish_actuator_command('fan', fan_state):
                        st.session_state['actuator_fan'] = fan_state
                        st.success(f"✅ Fan {'ON' if fan_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control Fan")
                
                # LED
                led_state = st.toggle(
                    "💡 Grow Light LED",
                    value=st.session_state['actuator_led'],
                    key='toggle_led'
                )
                if led_state != st.session_state['actuator_led']:
                    if publish_actuator_command('led', led_state):
                        st.session_state['actuator_led'] = led_state
                        st.success(f"✅ LED {'ON' if led_state else 'OFF'}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to control LED")
            
            st.markdown("---")
            
            # Current Status Summary
            st.markdown("### 📊 Current Status Summary")
            
            status_col1, status_col2, status_col3 = st.columns(3)
            
            with status_col1:
                active_count = sum([
                    st.session_state['actuator_pump_nutrition_AB'],
                    st.session_state['actuator_pump_water'],
                ])
                st.metric("💧 Pumps Active", f"{active_count}/2")
            
            with status_col2:
                ph_count = sum([
                    st.session_state['actuator_pump_Ph_Up'],
                    st.session_state['actuator_pump_Ph_Down'],
                ])
                st.metric("⚗️ pH Pumps Active", f"{ph_count}/2")
            
            with status_col3:
                util_count = sum([
                    st.session_state['actuator_fan'],
                    st.session_state['actuator_led'],
                ])
                st.metric("⚡ Utilities Active", f"{util_count}/2")
            
            st.info("💡 **Tip:** Commands are sent via MQTT to `iot/actuator/control` topic")

    # ============================================================
    # TAB 3: SENSOR TRENDS
    # ============================================================
    
    with tab3:
        if not df_log.empty:
            st.subheader("📈 Sensor Data Trends")
            
            # Temperature Trends
            st.markdown("### 🌡️ Temperature Monitoring")
            temp_chart = create_temperature_trend_chart(df_log)
            if temp_chart:
                st.plotly_chart(temp_chart, use_container_width=True)

            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⚗️ pH & TDS Levels")
                ph_tds_chart = create_ph_tds_chart(df_log)
                if ph_tds_chart:
                    st.plotly_chart(ph_tds_chart, use_container_width=True)
            
            with col2:
                st.markdown("### 💧 Water Monitoring")
                water_chart = create_water_level_chart(df_log)
                if water_chart:
                    st.plotly_chart(water_chart, use_container_width=True)

            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("### 💨 Humidity Trend")
                humidity_chart = create_humidity_chart(df_log)
                if humidity_chart:
                    st.plotly_chart(humidity_chart, use_container_width=True)
            
            with col4:
                st.markdown("### 💡 Light Intensity")
                light_chart = create_light_chart(df_log)
                if light_chart:
                    st.plotly_chart(light_chart, use_container_width=True)

        else:
            st.info("📝 No historical data available yet")

    # ============================================================
    # TAB 4: ANALYSIS
    # ============================================================
    
    with tab4:
        if not df_log.empty:
            st.subheader("📊 Statistical Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📝 Total Records", len(df_log))
                
                if 'status' in df_log.columns:
                    counts = df_log['status'].value_counts()
                    st.markdown("**Status Distribution:**")
                    subcol1, subcol2, subcol3 = st.columns(3)
                    with subcol1:
                        st.metric("🚨 Critical", counts.get('Critical', 0))
                    with subcol2:
                        st.metric("✅ Optimal", counts.get('Optimal', 0))
                    with subcol3:
                        st.metric("⚠️ Warning", counts.get('Warning', 0))
            
            with col2:
                status_pie = create_status_pie_chart(df_log)
                if status_pie:
                    st.plotly_chart(status_pie, use_container_width=True)

            st.markdown("---")

            st.subheader("🎯 ML Prediction Distributions")
            label_charts = create_label_distribution_charts(df_log)
            if label_charts:
                st.plotly_chart(label_charts, use_container_width=True)

            st.markdown("---")

            st.subheader("🔗 Sensor Correlation Analysis")
            corr_heatmap = create_correlation_heatmap(df_log)
            if corr_heatmap:
                st.plotly_chart(corr_heatmap, use_container_width=True)
                st.caption("Correlation shows relationships between different sensor readings")

        else:
            st.info("📝 No data available for analysis yet")

    # ============================================================
    # TAB 5: DATA LOG
    # ============================================================
    
    with tab5:
        st.subheader("📋 Historical Data Log")
        
        if not df_log.empty:
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.download_button(
                    label="📥 Download Full Log",
                    data=df_log.to_csv(index=False),
                    file_name=f"hydroponic_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            with col2:
                if st.button("🗑️ Clear Log"):
                    if os.path.exists(LOG_FILE):
                        os.remove(LOG_FILE)
                        st.success("Log cleared!")
                        st.rerun()

            st.caption(f"Showing last 100 entries | Total: {len(df_log)} records")
            
            display_df = df_log.tail(100).sort_values('timestamp', ascending=False)
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                height=600
            )

        else:
            st.info("📝 No log data available")
            st.caption("Data will appear here once MQTT messages are received and logged")

    # ============================================================
    # FOOTER
    # ============================================================
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("💡 ESP32 → MQTT → ML Inference → Action")
    with col2:
        st.caption(f"🔄 Auto-refresh: 3s | Log: {st.session_state['log_interval']}s")
    with col3:
        if st.session_state['manual_mode']:
            st.caption("🎮 Mode: MANUAL CONTROL")
        else:
            st.caption("🤖 Mode: AUTO (ML)")

    # Auto-refresh
    time.sleep(3)
    st.rerun()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()