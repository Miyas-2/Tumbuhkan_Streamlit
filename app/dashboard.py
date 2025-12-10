"""
IoT Hydroponics Monitoring Dashboard - Main Application
Modular version with comprehensive visualizations
"""
import streamlit as st
import os
import time
import atexit
from datetime import datetime

# Import modules
from config import (MQTT_BROKER, MQTT_TOPIC_SENSOR, MQTT_TOPIC_OUTPUT, MQTT_TOPIC_ACTUATOR,
                   LOG_FILE, FLAG_FILE, DEFAULT_LOG_INTERVAL_SECONDS, ACTUATOR_NAMES)
from model_handler import load_model
from mqtt_handler import get_mqtt_client
from data_logger import load_latest_prediction, load_log_data, load_latest_actuator
from utils import get_label_color
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
    st.markdown("**Real-time Multi-Sensor Monitoring with ML Prediction**")
    st.markdown("---")

    # Session State
    if 'log_interval' not in st.session_state:
        st.session_state['log_interval'] = DEFAULT_LOG_INTERVAL_SECONDS
    if 'mqtt_initialized' not in st.session_state:
        st.session_state.mqtt_initialized = False

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
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()

    # ============================================================
    # MAIN CONTENT
    # ============================================================

    # Load latest data
    data = load_latest_prediction()
    df_log = load_log_data()
    actuator_data = load_latest_actuator()  # NEW

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Real-time Monitor", 
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

            # NEW: Actuator Status Display
            st.markdown("---")
            st.subheader("🔧 Actuator Status")
            
            if actuator_data:
                st.caption(f"Last Updated: {actuator_data.get('timestamp', '—')}")
                
                act_col1, act_col2, act_col3 = st.columns(3)
                
                with act_col1:
                    # Nutrition Pump
                    nutrition_status = actuator_data.get('pump_nutrition_AB', False)
                    if nutrition_status:
                        st.success(f"🧪 **Nutrition Pump A+B:** ✅ ON")
                    else:
                        st.info(f"🧪 **Nutrition Pump A+B:** ⭕ OFF")
                    
                    # Water Pump
                    water_pump_status = actuator_data.get('pump_water', False)
                    if water_pump_status:
                        st.success(f"💧 **Water Pump:** ✅ ON")
                    else:
                        st.info(f"💧 **Water Pump:** ⭕ OFF")
                
                with act_col2:
                    # pH Up Pump
                    ph_up_status = actuator_data.get('pump_Ph_Up', False)
                    if ph_up_status:
                        st.success(f"⬆️ **pH Up Pump:** ✅ ON")
                    else:
                        st.info(f"⬆️ **pH Up Pump:** ⭕ OFF")
                    
                    # pH Down Pump
                    ph_down_status = actuator_data.get('pump_Ph_Down', False)
                    if ph_down_status:
                        st.success(f"⬇️ **pH Down Pump:** ✅ ON")
                    else:
                        st.info(f"⬇️ **pH Down Pump:** ⭕ OFF")
                
                with act_col3:
                    # Fan
                    fan_status = actuator_data.get('fan', False)
                    if fan_status:
                        st.success(f"🌀 **Cooling Fan:** ✅ ON")
                    else:
                        st.info(f"🌀 **Cooling Fan:** ⭕ OFF")
                    
                    # LED
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

    # TAB 2, 3, 4 tetap sama seperti sebelumnya...
    # [Copy dari kode sebelumnya untuk tab2, tab3, tab4]

    with tab2:
        if not df_log.empty:
            st.subheader("📈 Sensor Data Trends")
            
            # Temperature Trends
            st.markdown("### 🌡️ Temperature Monitoring")
            temp_chart = create_temperature_trend_chart(df_log)
            if temp_chart:
                st.plotly_chart(temp_chart, use_container_width=True)

            col1, col2 = st.columns(2)
            
            with col1:
                # pH and TDS
                st.markdown("### ⚗️ pH & TDS Levels")
                ph_tds_chart = create_ph_tds_chart(df_log)
                if ph_tds_chart:
                    st.plotly_chart(ph_tds_chart, use_container_width=True)
            
            with col2:
                # Water Level & Flow
                st.markdown("### 💧 Water Monitoring")
                water_chart = create_water_level_chart(df_log)
                if water_chart:
                    st.plotly_chart(water_chart, use_container_width=True)

            col3, col4 = st.columns(2)
            
            with col3:
                # Humidity
                st.markdown("### 💨 Humidity Trend")
                humidity_chart = create_humidity_chart(df_log)
                if humidity_chart:
                    st.plotly_chart(humidity_chart, use_container_width=True)
            
            with col4:
                # Light
                st.markdown("### 💡 Light Intensity")
                light_chart = create_light_chart(df_log)
                if light_chart:
                    st.plotly_chart(light_chart, use_container_width=True)

        else:
            st.info("📝 No historical data available yet")

    with tab3:
        if not df_log.empty:
            # Statistics
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
                # Status Pie Chart
                status_pie = create_status_pie_chart(df_log)
                if status_pie:
                    st.plotly_chart(status_pie, use_container_width=True)

            st.markdown("---")

            # Label Distributions
            st.subheader("🎯 ML Prediction Distributions")
            label_charts = create_label_distribution_charts(df_log)
            if label_charts:
                st.plotly_chart(label_charts, use_container_width=True)

            st.markdown("---")

            # Correlation Matrix
            st.subheader("🔗 Sensor Correlation Analysis")
            corr_heatmap = create_correlation_heatmap(df_log)
            if corr_heatmap:
                st.plotly_chart(corr_heatmap, use_container_width=True)
                st.caption("Correlation shows relationships between different sensor readings")

        else:
            st.info("📝 No data available for analysis yet")

    with tab4:
        st.subheader("📋 Historical Data Log")
        
        if not df_log.empty:
            # Download button
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
            
            # Display data table
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
        st.caption(f"🔄 Auto-refresh: 3s | Log interval: {st.session_state['log_interval']}s")
    with col3:
        st.caption("🤖 Powered by Random Forest ML Model")

    # Auto-refresh
    time.sleep(3)
    st.rerun()

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()