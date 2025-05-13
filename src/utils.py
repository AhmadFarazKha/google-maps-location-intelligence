# src/utils.py

def format_address(address_components):
    """Format address components into a readable string"""
    if not address_components:
        return "Unknown address"
    return ", ".join(address_components)

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = radians(lat1)
    lng1_rad = radians(lng1)
    lat2_rad = radians(lat2)
    lng2_rad = radians(lng2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    
    return distance