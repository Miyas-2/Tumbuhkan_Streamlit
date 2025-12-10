"""
ML Model handling untuk IoT Hydroponics Dashboard
"""
import streamlit as st
import joblib
import pandas as pd
from config import MODEL_PATH, PH_LABELS, TDS_LABELS, AMBIENT_LABELS, LIGHT_LABELS

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

        # Pastikan hanya fitur yang dipakai untuk training
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
        
        return {
            'ph_label': PH_LABELS.get(prediction[0], 'Unknown'),
            'tds_label': TDS_LABELS.get(prediction[1], 'Unknown'),
            'ambient_label': AMBIENT_LABELS.get(prediction[2], 'Unknown'),
            'light_label': LIGHT_LABELS.get(prediction[3], 'Unknown'),
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