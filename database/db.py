# database/db.py
import sqlite3
import os

DB_PATH = "crop_data.db"

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Updated table schema to match Excel
    c.execute('''CREATE TABLE IF NOT EXISTS crops (
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
    
    conn.commit()
    conn.close()

# Initialize on import
initialize_db()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn