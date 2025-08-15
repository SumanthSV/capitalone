# import_crops.py
import sqlite3
import pandas as pd
import re
from database.db import DB_PATH

def parse_range(value):
    """Parse range values with special characters like >, <, or -"""
    try:
        # Handle empty values
        if pd.isna(value):
            return None, None
        
        value = str(value).strip()
        
        # Handle greater than
        if value.startswith('>'):
            num = float(value[1:])
            return num, 10000  # Arbitrary high value
        
        # Handle less than
        if value.startswith('<'):
            num = float(value[1:])
            return 0, num
        
        # Handle single value
        if re.match(r'^\d+$', value):
            num = float(value)
            return num, num
        
        # Handle ranges with hyphen
        if '-' in value:
            parts = value.split('-')
            return float(parts[0].strip()), float(parts[1].strip())
        
        # Default to single value
        return float(value), float(value)
    except:
        return None, None

def import_excel_to_db():
    # Read Excel file
    df = pd.read_excel('crops_dataset.xlsx')
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create table with matching schema
    c.execute('''DROP TABLE IF EXISTS crops''')
    c.execute('''CREATE TABLE crops (
        id INTEGER PRIMARY KEY,
        name TEXT,
        sci_name TEXT,
        temp_min REAL,
        temp_max REAL,
        rainfall_min REAL,
        rainfall_max REAL,
        soil_ph_min REAL,
        soil_ph_max REAL,
        soil_texture TEXT,
        drainage TEXT,
        altitude_min REAL,
        altitude_max REAL,
        season TEXT,
        special_requirements TEXT
    )''')
    
    # Process and insert data
    for _, row in df.iterrows():
        # Parse all range values
        temp_min, temp_max = parse_range(row['Temp (°C)'])
        rainfall_min, rainfall_max = parse_range(row['Rainfall (mm)'])
        soil_ph_min, soil_ph_max = parse_range(row['Soil pH'])
        altitude_min, altitude_max = parse_range(row['Altitude (m)'])
        
        # Insert into database
        c.execute('''INSERT INTO crops (
            name, sci_name, temp_min, temp_max, 
            rainfall_min, rainfall_max, soil_ph_min, soil_ph_max,
            soil_texture, drainage, altitude_min, altitude_max,
            season, special_requirements
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            row['Crop Name'],
            row['Scientific Name'],
            temp_min,
            temp_max,
            rainfall_min,
            rainfall_max,
            soil_ph_min,
            soil_ph_max,
            row['Soil Texture'],
            row['Drainage'],
            altitude_min,
            altitude_max,
            row['Season'],
            row['Special Requirements']
        ))
    
    conn.commit()
    print(f"Imported {len(df)} crops successfully!")
    conn.close()

if __name__ == "__main__":
    import_excel_to_db()