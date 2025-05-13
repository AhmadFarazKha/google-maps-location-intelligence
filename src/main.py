# Google Maps Location Intelligence Tool
# main.py

import os
import folium
import pandas as pd
import requests
import json
from dotenv import load_dotenv
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
import certifi
import ssl

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class LocationIntelligenceTool:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        
        # Create SSL context with certifi certificates
        ctx = ssl.create_default_context(cafile=certifi.where())
        
        # Configure geocoder with SSL context
        self.geolocator = Nominatim(
            user_agent="location_intelligence_app",
            ssl_context=ctx
        )
        
    def search_places(self, location, radius=1000, place_type="restaurant"):
        """
        Search for places of a specific type near a location
        
        Args:
            location (str): The location to search around (e.g., "San Francisco, CA")
            radius (int): Radius in meters to search (max 50000)
            place_type (str): Type of place to search for (e.g., "restaurant", "software_company")
            
        Returns:
            list: List of places with their details
        """
        try:
            # Use Google's Geocoding API instead of relying on Nominatim
            geocode_endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location,
                "key": self.api_key
            }
            
            geocode_response = requests.get(geocode_endpoint, params=params, verify=True)
            geocode_data = geocode_response.json()
            
            if geocode_data.get("status") != "OK":
                print(f"Geocoding error: {geocode_data.get('status')}")
                return {"error": "Location not found"}
            
            location_result = geocode_data["results"][0]
            latitude = location_result["geometry"]["location"]["lat"]
            longitude = location_result["geometry"]["location"]["lng"]
            
            print(f"Successfully geocoded {location} to coordinates: {latitude}, {longitude}")
            
            # Use Google Places API to find places
            endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius,
                "type": place_type,
                "key": self.api_key
            }
            
            response = requests.get(endpoint_url, params=params, verify=True)
            places_data = response.json()
            
            if places_data.get("status") != "OK":
                print(f"Places API error: {places_data.get('status')}")
                if places_data.get("error_message"):
                    print(f"Error message: {places_data.get('error_message')}")
                return {"error": f"API error: {places_data.get('status')}"}
            
            results = places_data.get('results', [])
            
            places = []
            for place in results:
                places.append({
                    "name": place.get("name"),
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"],
                    "rating": place.get("rating", "N/A"),
                    "address": place.get("vicinity")
                })
                
            return places
            
        except Exception as e:
            print(f"Error in search_places: {str(e)}")
            return {"error": str(e)}
    
    def create_heatmap(self, places, location_name, zoom_start=13):
        """
        Create a heatmap visualization of places
        
        Args:
            places (list): List of places with lat/lng coordinates
            location_name (str): Name of the central location
            zoom_start (int): Initial zoom level for the map
            
        Returns:
            folium.Map: A Folium map object with heatmap
        """
        if not isinstance(places, list) or not places:
            print("No valid places data for heatmap creation")
            return None
            
        try:
            # Use Google's Geocoding API for consistent results
            geocode_endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location_name,
                "key": self.api_key
            }
            
            geocode_response = requests.get(geocode_endpoint, params=params, verify=True)
            geocode_data = geocode_response.json()
            
            if geocode_data.get("status") != "OK":
                print(f"Geocoding error in create_heatmap: {geocode_data.get('status')}")
                # Use first place as center if geocoding fails
                center_lat = places[0]["lat"]
                center_lng = places[0]["lng"]
            else:
                location_result = geocode_data["results"][0]
                center_lat = location_result["geometry"]["location"]["lat"]
                center_lng = location_result["geometry"]["location"]["lng"]
            
            # Create base map
            m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start)
            
            # Extract coordinates for heatmap
            heat_data = [[place["lat"], place["lng"]] for place in places]
            
            # Add heatmap layer
            HeatMap(heat_data).add_to(m)
            
            # Add markers for each location
            for place in places:
                popup_text = f"""
                    <b>{place['name']}</b><br>
                    Rating: {place['rating']}<br>
                    Address: {place['address']}
                """
                folium.Marker(
                    [place["lat"], place["lng"]], 
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=place["name"]
                ).add_to(m)
                
            return m
        except Exception as e:
            print(f"Error in create_heatmap: {str(e)}")
            return None
    
    def save_heatmap(self, heatmap, filename="heatmap.html"):
        """Save the heatmap to an HTML file"""
        if heatmap:
            try:
                heatmap.save(filename)
                print(f"Heatmap saved as {filename}")
                return f"Heatmap saved as {filename}"
            except Exception as e:
                print(f"Error saving heatmap: {str(e)}")
                return f"Error saving heatmap: {str(e)}"
        return "No heatmap to save"
    
    def export_data(self, places, filename="places_data.csv"):
        """Export the data to a CSV file"""
        if isinstance(places, list) and places:
            try:
                df = pd.DataFrame(places)
                df.to_csv(filename, index=False)
                print(f"Data exported to {filename}")
                return f"Data exported to {filename}"
            except Exception as e:
                print(f"Error exporting data: {str(e)}")
                return f"Error exporting data: {str(e)}"
        return "No data to export"

    def analyze_density(self, places, grid_size=5):
        """
        Analyze the density of places in a grid
        
        Args:
            places (list): List of places with lat/lng coordinates
            grid_size (int): Size of the grid for analysis
            
        Returns:
            dict: Density analysis results
        """
        if not isinstance(places, list) or not places:
            return {"error": "No places to analyze"}
            
        try:
            # Find bounding box
            lats = [place["lat"] for place in places]
            lngs = [place["lng"] for place in places]
            
            min_lat, max_lat = min(lats), max(lats)
            min_lng, max_lng = min(lngs), max(lngs)
            
            # Create grid
            lat_step = (max_lat - min_lat) / grid_size if max_lat != min_lat else 0.01
            lng_step = (max_lng - min_lng) / grid_size if max_lng != min_lng else 0.01
            
            grid_counts = {}
            
            for place in places:
                lat_bin = int((place["lat"] - min_lat) / lat_step) if lat_step != 0 else 0
                lng_bin = int((place["lng"] - min_lng) / lng_step) if lng_step != 0 else 0
                
                if lat_bin >= grid_size:
                    lat_bin = grid_size - 1
                if lng_bin >= grid_size:
                    lng_bin = grid_size - 1
                    
                grid_key = f"{lat_bin},{lng_bin}"
                grid_counts[grid_key] = grid_counts.get(grid_key, 0) + 1
            
            # Find hotspots (grid cells with most places)
            hotspots = sorted(grid_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate hotspot center coordinates
            hotspot_details = []
            for grid_key, count in hotspots[:3]:  # Top 3 hotspots
                lat_bin, lng_bin = map(int, grid_key.split(','))
                center_lat = min_lat + (lat_bin + 0.5) * lat_step
                center_lng = min_lng + (lng_bin + 0.5) * lng_step
                
                location_name = self.reverse_geocode(center_lat, center_lng)
                
                hotspot_details.append({
                    "grid_cell": grid_key,
                    "count": count,
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "approximate_location": location_name
                })
                
            return {
                "total_places": len(places),
                "grid_size": grid_size,
                "hotspots": hotspot_details
            }
        except Exception as e:
            print(f"Error in analyze_density: {str(e)}")
            return {"error": str(e)}
    
    def reverse_geocode(self, lat, lng):
        """Get address from latitude and longitude"""
        try:
            # Use Google's Reverse Geocoding API for consistency
            endpoint_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lng}",
                "key": self.api_key
            }
            
            response = requests.get(endpoint_url, params=params, verify=True)
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                return data["results"][0].get("formatted_address", "Unknown location")
            return "Unknown location"
        except Exception as e:
            print(f"Error in reverse_geocode: {str(e)}")
            return "Unknown location"


# Example usage
if __name__ == "__main__":
    tool = LocationIntelligenceTool()
    
    # Check if API key is set
    if not GOOGLE_API_KEY:
        print("ERROR: Google API key is not set in .env file")
        print("Please add your Google API key to .env file: GOOGLE_API_KEY=your_key_here")
        exit(1)
    
    print(f"Starting location intelligence analysis...")
    
    # Allow user to specify location
    search_location = input("Enter location to analyze (default: San Francisco, CA): ") or "San Francisco, CA"
    search_radius = int(input("Enter search radius in meters (default: 5000): ") or "5000")
    
    # Search for software companies in a location
    print(f"\nSearching for software companies in {search_location}...")
    software_places = tool.search_places(
        location=search_location, 
        radius=search_radius, 
        place_type="software_company"
    )
    
    # Create and save heatmap
    if isinstance(software_places, list) and software_places:
        print(f"Found {len(software_places)} software companies.")
        heatmap = tool.create_heatmap(software_places, search_location)
        tool.save_heatmap(heatmap, "software_companies_heatmap.html")
        tool.export_data(software_places, "software_companies_data.csv")
        
        # Analyze density
        analysis = tool.analyze_density(software_places)
        print("\nHotspot Analysis:")
        for i, hotspot in enumerate(analysis.get("hotspots", [])[:3], 1):
            print(f"Hotspot #{i}: {hotspot['count']} places near {hotspot['approximate_location']}")
    elif isinstance(software_places, dict) and software_places.get("error"):
        print(f"Error finding software companies: {software_places['error']}")
    else:
        print("No software companies found.")
    
    # Search for restaurants/food streets
    print(f"\nSearching for restaurants in {search_location}...")
    food_places = tool.search_places(
        location=search_location, 
        radius=search_radius, 
        place_type="restaurant"
    )
    
    # Create and save heatmap for food places
    if isinstance(food_places, list) and food_places:
        print(f"Found {len(food_places)} restaurants.")
        food_heatmap = tool.create_heatmap(food_places, search_location)
        tool.save_heatmap(food_heatmap, "food_streets_heatmap.html")
        tool.export_data(food_places, "food_places_data.csv")
        
        # Analyze density
        food_analysis = tool.analyze_density(food_places)
        print("\nFood Street Analysis:")
        for i, hotspot in enumerate(food_analysis.get("hotspots", [])[:3], 1):
            print(f"Food Hotspot #{i}: {hotspot['count']} places near {hotspot['approximate_location']}")
    elif isinstance(food_places, dict) and food_places.get("error"):
        print(f"Error finding restaurants: {food_places['error']}")
    else:
        print("No restaurants found.")
    
    print("\nAnalysis complete! Check the generated HTML and CSV files in your project directory.")
    