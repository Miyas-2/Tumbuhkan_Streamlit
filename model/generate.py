import pandas as pd
import random
from datetime import datetime, timedelta

# ================================
# CONFIGURATION
# ================================
TOTAL_ROWS = 1500
START_TIME = datetime.now()

data = []

# ================================
# STRATEGI: Generate data untuk setiap kombinasi label
# ================================
# Total kombinasi: 5 (pH) × 5 (TDS) × 3 (Ambient) × 3 (Light) = 225 kombinasi
# Kita akan generate minimal 6-7 sample per kombinasi

# Define target ranges untuk setiap label class
pH_RANGES = {
    0: (4.0, 5.4),      # Too Low
    1: (5.5, 5.9),      # Low
    2: (6.0, 6.8),      # Normal
    3: (6.9, 7.2),      # High
    4: (7.3, 8.5)       # Too High
}

TDS_RANGES = {
    0: (300, 550),      # Too Low
    1: (560, 1040),     # Low
    2: (1050, 1680),    # Normal
    3: (1681, 2100),    # High
    4: (2110, 2500)     # Too High
}

# Ambient: kombinasi temp + humidity
AMBIENT_CONFIGS = {
    0: {  # Bad
        'temp': [(14, 15.9), (32.1, 34)],  # extreme temps
        'humidity': [(33, 34.9), (80.1, 85)]  # extreme humidity
    },
    1: {  # Slightly Off
        'temp': [(16, 17.9), (28.1, 32)],  # moderate deviation
        'humidity': [(35, 39.9), (70.1, 80)]
    },
    2: {  # Ideal
        'temp': [(18, 28)],
        'humidity': [(40, 70)]
    }
}

LDR_RANGES = {
    0: (50, 499),       # Too Dark
    1: (500, 2500),     # Normal
    2: (2501, 4000)     # Too Bright
}

# Water temperature untuk adjustment
WATER_TEMP_LOW = (20, 28)   # tidak trigger adjustment
WATER_TEMP_HIGH = (28.1, 30) # trigger adjustment

row_id = 1

# Generate untuk setiap kombinasi label
for ph_label in range(5):
    for tds_label in range(5):
        for ambient_label in range(3):
            for light_label in range(3):
                
                # Generate 6-7 samples untuk setiap kombinasi
                samples_per_combo = random.randint(6, 7)
                
                for _ in range(samples_per_combo):
                    if row_id > TOTAL_ROWS:
                        break
                    
                    timestamp = START_TIME + timedelta(seconds=row_id*30)
                    
                    # Generate pH
                    ph_range = pH_RANGES[ph_label]
                    ph = round(random.uniform(ph_range[0], ph_range[1]), 2)
                    
                    # Generate TDS (consider adjustment for water temp)
                    tds_range = TDS_RANGES[tds_label]
                    # Jika target tds_label butuh adjustment, generate nilai lebih tinggi
                    use_high_water_temp = random.choice([True, False])
                    if use_high_water_temp:
                        water_temperature = round(random.uniform(28.1, 30), 2)
                        # Add offset untuk compensate adjustment
                        tds = int(random.uniform(tds_range[0] + 40, tds_range[1] + 70))
                    else:
                        water_temperature = round(random.uniform(20, 28), 2)
                        tds = int(random.uniform(tds_range[0], tds_range[1]))
                    
                    # Generate Ambient (temperature + humidity)
                    ambient_config = AMBIENT_CONFIGS[ambient_label]
                    
                    # Pilih salah satu range untuk temp dan humidity
                    temp_ranges = ambient_config['temp']
                    humidity_ranges = ambient_config['humidity']
                    
                    temp_range = random.choice(temp_ranges)
                    humidity_range = random.choice(humidity_ranges)
                    
                    air_temperature = round(random.uniform(temp_range[0], temp_range[1]), 2)
                    air_humidity = round(random.uniform(humidity_range[0], humidity_range[1]), 2)
                    
                    # Generate LDR
                    ldr_range = LDR_RANGES[light_label]
                    ldr_value = int(random.uniform(ldr_range[0], ldr_range[1]))
                    
                    # Generate water flow (random, tidak affect label)
                    water_flow = round(random.uniform(8.0, 15.0), 2)
                    
                    # Generate water level (random, tidak affect label)
                    water_level = round(random.uniform(10.0, 15.0), 2)
                    
                    data.append([
                        row_id,
                        timestamp,
                        ph,
                        tds,
                        water_flow,
                        air_humidity,
                        air_temperature,
                        ldr_value,
                        water_temperature,
                        water_level
                    ])
                    
                    row_id += 1
                
                if row_id > TOTAL_ROWS:
                    break
            if row_id > TOTAL_ROWS:
                break
        if row_id > TOTAL_ROWS:
            break
    if row_id > TOTAL_ROWS:
        break

# Shuffle data agar tidak terurut berdasarkan label
random.shuffle(data)

# Re-assign ID dan timestamp setelah shuffle
for i, row in enumerate(data, 1):
    row[0] = i  # Update ID
    row[1] = START_TIME + timedelta(seconds=i*30)  # Update timestamp

# ================================
# CREATE DATAFRAME
# ================================
columns = [
    "id",
    "timestamp",
    "ph",
    "tds",
    "water_flow",
    "air_humidity",
    "air_temperature",
    "ldr_value",
    "water_temperature",
    "water_level"
]

df = pd.DataFrame(data, columns=columns)

# ================================
# SAVE TO CSV
# ================================
df.to_csv("hydroponic_dummy_data.csv", index=False)

print("✅ Dummy dataset successfully generated: hydroponic_dummy_data.csv")
print(f"📊 Total rows: {len(df)}")
print("\n📋 Sample data:")
print(df.head(10))
print("\n📈 Value ranges:")
print(f"pH: {df['ph'].min():.2f} - {df['ph'].max():.2f}")
print(f"TDS: {df['tds'].min()} - {df['tds'].max()}")
print(f"Air Temp: {df['air_temperature'].min():.2f} - {df['air_temperature'].max():.2f}")
print(f"Air Humidity: {df['air_humidity'].min():.2f} - {df['air_humidity'].max():.2f}")
print(f"LDR: {df['ldr_value'].min()} - {df['ldr_value'].max()}")
print(f"Water Temp: {df['water_temperature'].min():.2f} - {df['water_temperature'].max():.2f}")