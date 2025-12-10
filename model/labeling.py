import pandas as pd
import numpy as np

def label_ph(ph_value, water_temp):
    """
    Label pH dengan 5 classes
    Jika water temperature > 28°C, kurangi 0.1-0.2 dari pH
    """
    # Adjust pH jika water temperature tinggi
    if water_temp > 28:
        ph_adjusted = ph_value - np.random.uniform(0.1, 0.2)
    else:
        ph_adjusted = ph_value
    
    # Labeling
    if ph_adjusted < 5.5:
        return 0  # Too Low
    elif 5.5 <= ph_adjusted < 6.0:
        return 1  # Low
    elif 6.0 <= ph_adjusted <= 6.8:
        return 2  # Normal ✅
    elif 6.9 <= ph_adjusted <= 7.2:
        return 3  # High
    else:  # > 7.2
        return 4  # Too High


def label_tds(tds_value, water_temp):
    """
    Label TDS/PPM dengan 5 classes
    Jika water temperature > 28°C, kurangi 40-70 ppm
    """
    # Adjust TDS jika water temperature tinggi
    if water_temp > 28:
        tds_adjusted = tds_value - np.random.uniform(40, 70)
    else:
        tds_adjusted = tds_value
    
    # Labeling
    if tds_adjusted < 560:
        return 0  # Too Low
    elif 560 <= tds_adjusted < 1050:
        return 1  # Low
    elif 1050 <= tds_adjusted <= 1680:
        return 2  # Normal ✅
    elif 1681 <= tds_adjusted <= 2100:
        return 3  # High
    else:  # > 2100
        return 4  # Too High


def label_ambient(air_temp, air_humidity):
    """
    Label ambient (kombinasi temperature + humidity) dengan 3 classes
    Ideal: 18-28°C dan 40-70% humidity
    """
    temp_ideal = 18 <= air_temp <= 28
    humidity_ideal = 40 <= air_humidity <= 70
    
    if temp_ideal and humidity_ideal:
        return 2  # Ideal ✅
    
    # Bad conditions (extreme)
    temp_bad = air_temp < 16 or air_temp > 32
    humidity_bad = air_humidity < 35 or air_humidity > 80
    
    if temp_bad or humidity_bad:
        return 0  # Bad
    
    # Slightly off (moderate deviation)
    return 1  # Slightly Off


def label_light(ldr_value):
    """
    Label LDR dengan 3 classes
    """
    if ldr_value < 500:
        return 0  # Too Dark
    elif 500 <= ldr_value <= 2500:
        return 1  # Normal ✅
    else:  # > 2500
        return 2  # Too Bright


def add_labels_to_dataset(input_csv='hydroponic_dummy_data.csv', 
                         output_csv='hydroponic_labeled_data.csv'):
    """
    Membaca CSV, menambahkan label, dan menyimpan hasil
    """
    # Baca data
    df = pd.read_csv(input_csv)
    
    # Tambahkan kolom label
    df['ph_label'] = df.apply(lambda row: label_ph(row['ph'], row['water_temperature']), axis=1)
    df['tds_label'] = df.apply(lambda row: label_tds(row['tds'], row['water_temperature']), axis=1)
    df['ambient_label'] = df.apply(lambda row: label_ambient(row['air_temperature'], row['air_humidity']), axis=1)
    df['light_label'] = df.apply(lambda row: label_light(row['ldr_value']), axis=1)
    
    # Simpan hasil
    df.to_csv(output_csv, index=False)
    
    # Tampilkan statistik
    print("✅ Labeling completed successfully!")
    print(f"📁 Output file: {output_csv}")
    print("\n📊 Label Distribution:")
    print("\n🔵 pH Label:")
    print(df['ph_label'].value_counts().sort_index())
    print("\n🟢 TDS Label:")
    print(df['tds_label'].value_counts().sort_index())
    print("\n🟡 Ambient Label:")
    print(df['ambient_label'].value_counts().sort_index())
    print("\n🟠 Light Label:")
    print(df['light_label'].value_counts().sort_index())
    
    # Tampilkan sample data
    print("\n📋 Sample of labeled data:")
    print(df[['ph', 'water_temperature', 'ph_label', 
              'tds', 'tds_label', 
              'air_temperature', 'air_humidity', 'ambient_label',
              'ldr_value', 'light_label']].head(10))
    
    return df


if __name__ == "__main__":
    # Jalankan labeling
    df_labeled = add_labels_to_dataset()
    
    print("\n✨ Done! Check 'hydroponic_labeled_data.csv' for the result.")