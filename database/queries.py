# database/queries.py
from database.db import get_connection

def get_crop_recommendations(params: dict) -> tuple:
    conditions = []
    query_params = {}
    
    # Temperature condition
    if params.get('temperature') is not None:
        conditions.append(":temperature BETWEEN temp_min AND temp_max")
        query_params['temperature'] = params['temperature']
    
    # Rainfall condition
    if params.get('rainfall') is not None:
        conditions.append(":rainfall BETWEEN rainfall_min AND rainfall_max")
        query_params['rainfall'] = params['rainfall']
    
    # Soil pH condition
    if params.get('soil_ph') is not None:
        conditions.append(":soil_ph BETWEEN soil_ph_min AND soil_ph_max")
        query_params['soil_ph'] = params['soil_ph']
    
    # Soil Type condition
    if params.get('soil_type') is not None:
        conditions.append("soil_texture = :soil_type")
        query_params['soil_type'] = params['soil_type']
    
    # Season condition
    if params.get('season') is not None:
        conditions.append("season LIKE '%' || :season || '%'")
        query_params['season'] = params['season']
    
    # Altitude condition
    if params.get('altitude') is not None:
        conditions.append(":altitude BETWEEN altitude_min AND altitude_max")
        query_params['altitude'] = params['altitude']
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"""
        SELECT name, sci_name, season, special_requirements 
        FROM crops 
        WHERE {where_clause}
        LIMIT 5
    """
    
    # Execute query
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, query_params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results, query