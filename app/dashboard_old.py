import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import joblib
from datetime import datetime
import os
import time
import atexit
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# KONFIGURASI MQTT & MODEL
# ============================================================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "iot/sensor/data"
MQTT_TOPIC_OUTPUT = "iot/output"
MODEL_PATH = "../model/hydroponic_multioutput_rf_model.pkl"  # FIXED: Relative path from app/
LOG_FILE = "prediction_log.csv"
LATEST_JSON = "latest_prediction.json"

# Konfigurasi Baru untuk Logging Interval
DEFAULT_LOG_INTERVAL_SECONDS = 5  # Default log setiap 5 detik

# ============================================================
# LOAD MODEL ML
# ============================================================

@st.cache_resource
def load_model():
    """Load model ML dari file pkl (joblib)"""
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✓ Model berhasil di-load dari {MODEL_PATH}")
        return model
    except Exception as e:
        print(f"✗ Gagal load model: {e}")
        return None

# ============================================================
# FUNGSI PREDIKSI
# ============================================================

def predict_condition(payload, model):
    """
    Prediksi kondisi berdasarkan payload lengkap (multifeature).
    Returns: dict dengan 4 labels atau "Unknown" jika model None
    """
    try:
        if model is None:
            return {
                'ph_label': 'Unknown',
                'tds_label': 'Unknown', 
                'ambient_label': 'Unknown',
                'light_label': 'Unknown'
            }

        # Pastikan hanya fitur yang dipakai untuk training (tanpa water_flow dan water_level)
        input_data = pd.DataFrame([{
            "ph": float(payload.get("ph", 0)),
            "tds": float(payload.get("tds", 0)),
            "water_temperature": float(payload.get("water_temperature", 0)),
            "air_humidity": float(payload.get("air_humidity", 0)),
            "air_temperature": float(payload.get("air_temperature", 0)),
            "ldr_value": float(payload.get("ldr_value", 0))
        }])

        # Prediksi menghasilkan array [ph_label, tds_label, ambient_label, light_label]
        prediction = model.predict(input_data)[0]
        
        # Label mapping
        ph_labels = {0: 'Too Low', 1: 'Low', 2: 'Normal', 3: 'High', 4: 'Too High'}
        tds_labels = {0: 'Too Low', 1: 'Low', 2: 'Normal', 3: 'High', 4: 'Too High'}
        ambient_labels = {0: 'Bad', 1: 'Slightly Off', 2: 'Ideal'}
        light_labels = {0: 'Too Dark', 1: 'Normal', 2: 'Too Bright'}
        
        return {
            'ph_label': ph_labels.get(prediction[0], 'Unknown'),
            'tds_label': tds_labels.get(prediction[1], 'Unknown'),
            'ambient_label': ambient_labels.get(prediction[2], 'Unknown'),
            'light_label': light_labels.get(prediction[3], 'Unknown'),
            'ph_value': prediction[0],
            'tds_value': prediction[1],
            'ambient_value': prediction[2],
            'light_value': prediction[3]
        }
    except Exception as e:
        print(f"Error saat prediksi: {e}")
        return {
            'ph_label': 'Error',
            'tds_label': 'Error',
            'ambient_label': 'Error',
            'light_label': 'Error'
        }

# ============================================================
# FUNGSI LOGGING KE CSV
# ============================================================

def log_prediction(data, status):
    """
    Simpan hasil prediksi ke CSV dengan semua 4 labels
    """
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

# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback saat koneksi berhasil"""
    if rc == 0:
        print(f"✓ Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC_SENSOR)
        print(f"📡 Subscribed to: {MQTT_TOPIC_SENSOR}")
    else:
        print(f"✗ Connection failed: {rc}")

def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def on_message(client, userdata, msg):
    """Callback saat terima message - process payload baru"""
    try:
        payload = json.loads(msg.payload.decode())

        # Ambil semua sensor dari payload
        ph = safe_float(payload.get("ph", 0))
        tds = safe_float(payload.get("tds", 0))
        water_flow = safe_float(payload.get("water_flow", 0))
        air_humidity = safe_float(payload.get("air_humidity", 0))
        air_temperature = safe_float(payload.get("air_temperature", 0))
        ldr = safe_float(payload.get("ldr_value", 0))
        water_temperature = safe_float(payload.get("water_temperature", 0))
        water_level = safe_float(payload.get("water_level", 0))

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 pH: {ph} | TDS: {tds} | WaterT: {water_temperature}°C | AirT: {air_temperature}°C | Hum: {air_humidity}% | LDR: {ldr}")

        # Ambil model dari userdata
        model = userdata.get('model') if isinstance(userdata, dict) else None

        # Prediksi - returns dict dengan 4 labels
        prediction_result = predict_condition(payload, model)
        
        # Extract labels
        ph_label = prediction_result.get('ph_label', 'Unknown')
        tds_label = prediction_result.get('tds_label', 'Unknown')
        ambient_label = prediction_result.get('ambient_label', 'Unknown')
        light_label = prediction_result.get('light_label', 'Unknown')
        
        # Tentukan status keseluruhan dan output
        # Status critical jika ada yang Too High/Too Low atau Bad
        critical_ph = ph_label in ['Too Low', 'Too High']
        critical_tds = tds_label in ['Too Low', 'Too High']
        critical_ambient = ambient_label == 'Bad'
        critical_light = light_label in ['Too Dark', 'Too Bright']
        
        if critical_ph or critical_tds or critical_ambient:
            output = "ALERT_CRITICAL"
            icon = "🚨"
            color = "red"
            status = "Critical"
        elif ph_label == 'Normal' and tds_label == 'Normal' and ambient_label == 'Ideal' and light_label == 'Normal':
            output = "ALL_NORMAL"
            icon = "✅"
            color = "green"
            status = "Optimal"
        else:
            output = "NEEDS_ATTENTION"
            icon = "⚠️"
            color = "orange"
            status = "Warning"

        # Publish output
        try:
            output_data = {
                "status": status,
                "ph": ph_label,
                "tds": tds_label,
                "ambient": ambient_label,
                "light": light_label,
                "action": output
            }
            client.publish(MQTT_TOPIC_OUTPUT, json.dumps(output_data))
        except Exception as e:
            print(f"✗ Gagal publish output: {e}")

        # Logging dengan interval
        current_time = time.time()
        log_interval = userdata.get('log_interval', DEFAULT_LOG_INTERVAL_SECONDS) if isinstance(userdata, dict) else DEFAULT_LOG_INTERVAL_SECONDS
        last_logged_time = userdata.get('last_logged_time', 0) if isinstance(userdata, dict) else 0
        should_log = (current_time - last_logged_time) >= log_interval

        if should_log:
            # Log ke CSV dengan semua label
            logged = log_prediction({
                "ph": ph,
                "tds": tds,
                "water_flow": water_flow,
                "air_humidity": air_humidity,
                "air_temperature": air_temperature,
                "ldr_value": ldr,
                "water_temperature": water_temperature,
                "water_level": water_level,
                "ph_label": ph_label,
                "tds_label": tds_label,
                "ambient_label": ambient_label,
                "light_label": light_label
            }, status)

            if isinstance(userdata, dict):
                userdata['last_logged_time'] = current_time
                client.user_data_set(userdata)

            if logged:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 LOGGED → {ph_label} | {tds_label} | {ambient_label} | {light_label}")

        # Simpan latest_prediction.json untuk UI
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ph": ph,
            "tds": tds,
            "water_flow": water_flow,
            "air_humidity": air_humidity,
            "air_temperature": air_temperature,
            "ldr_value": ldr,
            "water_temperature": water_temperature,
            "water_level": water_level,
            "ph_label": ph_label,
            "tds_label": tds_label,
            "ambient_label": ambient_label,
            "light_label": light_label,
            "status": status,
            "output": output,
            "icon": icon,
            "color": color
        }

        try:
            with open(LATEST_JSON, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"✗ Gagal simpan latest json: {e}")

    except Exception as e:
        print(f"✗ Error on_message: {e}")

def on_disconnect(client, userdata, rc, properties=None):
    """Callback saat disconnect"""
    if rc != 0:
        print(f"⚠️ Disconnected: {rc}")

# ============================================================
# MQTT CLIENT SETUP - PERSISTENT DENGAN FILE FLAG
# ============================================================

def get_mqtt_client(model, log_interval):
    """Get atau create MQTT client - persistent dengan file flag"""
    flag_file = 'mqtt_running.flag'

    if os.path.exists(flag_file):
        # Client sudah running, return None (skip create new)
        return None

    print("🔌 Creating new MQTT client...")

    # Buat client baru
    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"streamlit_iot_{int(time.time())}"
        )
    except Exception:
        # fallback jika versi callback tidak tersedia
        client = mqtt.Client(client_id=f"streamlit_iot_{int(time.time())}")

    # Set userdata - include model, log interval dan last log time
    userdata = {
        'model': model,
        'log_interval': log_interval,
        'last_logged_time': 0
    }
    client.user_data_set(userdata)

    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        # Create flag file
        with open(flag_file, 'w') as f:
            f.write(str(os.getpid()))

        print(f"✓ MQTT client connected with Log Interval: {log_interval}s")
        return client

    except Exception as e:
        print(f"✗ Failed connect MQTT: {e}")
        return None

# ============================================================
# LOAD LATEST PREDICTION DARI FILE
# ============================================================

def load_latest_prediction():
    """Load latest prediction dari file JSON"""
    try:
        if os.path.exists(LATEST_JSON):
            with open(LATEST_JSON, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

# ============================================================
# VISUALIZATIONS
# ============================================================

def create_temperature_trend_chart(df_log):
    """Create temperature trend chart (air_temperature)"""
    if df_log.empty:
        return None

    df_recent = df_log.tail(20).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    # Color mapping for status
    color_map = {
        'Critical': 'red', 
        'Optimal': 'green', 
        'Warning': 'orange'
    }
    
    # Gunakan status column jika ada, fallback ke default
    if 'status' in df_recent.columns:
        df_recent['color'] = df_recent['status'].map(color_map).fillna('gray')
    else:
        df_recent['color'] = 'steelblue'

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_recent['timestamp'],
        y=df_recent['air_temperature'],
        mode='lines+markers',
        name='Air Temperature',
        line=dict(width=2),
        marker=dict(
            color=df_recent['color'],
            size=8,
            line=dict(color='white', width=1)
        ),
        hovertemplate='<b>%{y:.1f}°C</b><br>%{x}<extra></extra>'
    ))

    fig.update_layout(
        title="Air Temperature Trend (Last 20 readings)",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        height=400,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

def create_prediction_pie_chart(df_log):
    """Create status distribution pie chart"""
    if df_log.empty:
        return None

    # Gunakan status column
    if 'status' not in df_log.columns:
        return None
        
    counts = df_log['status'].value_counts()
    colors = {
        'Critical': '#ff4444', 
        'Optimal': '#44ff44', 
        'Warning': '#ff9944'
    }
    
    fig = px.pie(
        values=counts.values,
        names=counts.index,
        title="Status Distribution",
        color=counts.index,
        color_discrete_map=colors
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    return fig

# ============================================================
# STREAMLIT UI
# ============================================================

def main():
    """Main function untuk Streamlit app"""
    st.set_page_config(
        page_title="IoT Monitoring System",
        page_icon="🌡️",
        layout="wide"
    )

    st.title("🌡️ IoT Hydroponics Monitoring (Multifeature)")
    st.markdown("**Real-time Sensor Monitoring with ML Prediction**")
    st.markdown("---")

    # Inisiasi Session State
    if 'log_interval' not in st.session_state:
        st.session_state['log_interval'] = DEFAULT_LOG_INTERVAL_SECONDS
    if 'mqtt_initialized' not in st.session_state:
        st.session_state.mqtt_initialized = False

    # Load model (cached)
    model = load_model()

    # Setup MQTT client hanya sekali, dengan interval log saat ini
    if not st.session_state.mqtt_initialized:
        mqtt_client = get_mqtt_client(model, st.session_state['log_interval'])
        if mqtt_client:
            st.session_state.mqtt_initialized = True
        time.sleep(1)

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"**MQTT Broker:** {MQTT_BROKER}")
        st.info(f"**Subscribe:** {MQTT_TOPIC_SENSOR}")
        st.info(f"**Publish:** {MQTT_TOPIC_OUTPUT}")

        st.markdown("---")
        st.header("💾 Log Settings")

        new_interval = st.number_input(
            "Interval Log ke CSV (detik)",
            min_value=1,
            max_value=3600,
            value=st.session_state['log_interval'],
            step=1,
            key='log_interval_input'
        )

        st.session_state['log_interval'] = new_interval

        if st.button("Apply Setting & Restart MQTT"):
            if os.path.exists('mqtt_running.flag'):
                try:
                    os.remove('mqtt_running.flag')
                except Exception:
                    pass
            st.session_state.mqtt_initialized = False
            st.info("Restarting MQTT Client...")
            st.rerun()

        st.markdown("---")
        st.header("📊 System Status")

        if model:
            st.success("✓ Model: Loaded")
        else:
            st.warning("⚠️ Model: Not Loaded (using no-predict behavior)")

        if os.path.exists('mqtt_running.flag'):
            st.success(f"✓ MQTT: Running (Log: {st.session_state['log_interval']}s)")
        else:
            st.warning("⚠️ MQTT: Not Running")
            if st.button("🔄 Start MQTT"):
                if os.path.exists('mqtt_running.flag'):
                    try:
                        os.remove('mqtt_running.flag')
                    except Exception:
                        pass
                st.session_state.mqtt_initialized = False
                st.rerun()

        if st.button("🔄 Refresh UI Only"):
            st.rerun()

    # Main content
    col1, col2 = st.columns(2)

    with col1:
        st.header("📡 Latest Sensor Data")
        data = load_latest_prediction()

        if data:
            # Show key metrics
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Air Temp", f"{data.get('air_temperature', '—')}°C")
                st.metric("Water Temp", f"{data.get('water_temperature', '—')}°C")
            with m2:
                st.metric("Air Hum", f"{data.get('air_humidity', '—')}%")
                st.metric("Water Level", f"{data.get('water_level', '—')} cm")
            with m3:
                st.metric("pH", data.get('ph', '—'))
                st.metric("TDS", f"{data.get('tds', '—')} ppm")

            # Prediction display - 4 labels
            st.markdown(f"### {data.get('icon', '')} Status: **{data.get('status', '—')}**")
            
            col_pred1, col_pred2, col_pred3, col_pred4 = st.columns(4)
            with col_pred1:
                ph_label = data.get('ph_label', '—')
                ph_color = 'green' if ph_label == 'Normal' else ('orange' if ph_label in ['Low', 'High'] else 'red')
                st.markdown(f"**pH:** :{ph_color}[{ph_label}]")
            
            with col_pred2:
                tds_label = data.get('tds_label', '—')
                tds_color = 'green' if tds_label == 'Normal' else ('orange' if tds_label in ['Low', 'High'] else 'red')
                st.markdown(f"**TDS:** :{tds_color}[{tds_label}]")
            
            with col_pred3:
                ambient_label = data.get('ambient_label', '—')
                ambient_color = 'green' if ambient_label == 'Ideal' else ('orange' if ambient_label == 'Slightly Off' else 'red')
                st.markdown(f"**Ambient:** :{ambient_color}[{ambient_label}]")
            
            with col_pred4:
                light_label = data.get('light_label', '—')
                light_color = 'green' if light_label == 'Normal' else 'orange'
                st.markdown(f"**Light:** :{light_color}[{light_label}]")
            
            st.info(f"Output: **{data.get('output', '—')}**")
            st.caption(f"Last Update: {data.get('timestamp', '—')}")
        else:
            st.info("⏳ Waiting for sensor data...")

    with col2:
        st.header("📈 Log Statistics")
        if os.path.exists(LOG_FILE):
            try:
                df_log = pd.read_csv(LOG_FILE)
                st.metric("Total Predictions Logged", len(df_log))
                st.caption(f"Logged every ~{st.session_state['log_interval']} seconds.")

                # Update untuk status baru
                if 'status' in df_log.columns:
                    counts = df_log['status'].value_counts()
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("🚨 Critical", counts.get('Critical', 0))
                    with c2:
                        st.metric("✅ Optimal", counts.get('Optimal', 0))
                    with c3:
                        st.metric("⚠️ Warning", counts.get('Warning', 0))
                else:
                    st.info("Old log format - delete prediction_log.csv to use new format")

                # Download button
                st.download_button(
                    label="📥 Download Log",
                    data=df_log.to_csv(index=False),
                    file_name=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error reading log: {e}")
                st.info("💡 Try deleting prediction_log.csv to reset")
        else:
            st.info("📝 No log yet")

    # Visualizations Section
    if os.path.exists(LOG_FILE):
        try:
            df_log = pd.read_csv(LOG_FILE)
            if not df_log.empty and 'status' in df_log.columns:
                st.markdown("---")
                st.header("📊 Data Visualizations")

                vis_col1, vis_col2 = st.columns(2)

                with vis_col1:
                    temp_chart = create_temperature_trend_chart(df_log)
                    if temp_chart:
                        st.plotly_chart(temp_chart, use_container_width=True)

                with vis_col2:
                    pie_chart = create_prediction_pie_chart(df_log)
                    if pie_chart:
                        st.plotly_chart(pie_chart, use_container_width=True)

                # Recent data table
                st.subheader("📋 Recent Log Entries")
                display_df = df_log.tail(10).sort_values('timestamp', ascending=False)
                st.dataframe(display_df, hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating visualizations: {e}")

    st.markdown("---")
    st.caption("💡 ESP32 → MQTT → ML Inference → Output Command")
    st.caption("🔄 Click 'Refresh UI Only' to update display")

    # Auto-refresh setiap 3 detik
    time.sleep(3)
    st.rerun()

# ============================================================
# CLEANUP ON EXIT
# ============================================================

def cleanup():
    """Cleanup saat aplikasi ditutup"""
    flag_file = 'mqtt_running.flag'
    if os.path.exists(flag_file):
        try:
            os.remove(flag_file)
            print("🧹 Cleanup: MQTT flag removed")
        except Exception as e:
            print(f"✗ Cleanup error: {e}")

atexit.register(cleanup)

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    main()