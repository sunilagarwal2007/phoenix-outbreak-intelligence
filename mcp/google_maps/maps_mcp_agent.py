"""
Google Maps MCP Agent for Phoenix Outbreak Intelligence
Provides geographic analysis, routing, and hotspot mapping capabilities
"""

import logging
from typing import Dict, List, Tuple, Optional
import googlemaps
import json
from datetime import datetime

class GoogleMapsMCPAgent:
    """
    Model Context Protocol agent for Google Maps integration
    
    Capabilities:
    - Geographic coordinate resolution
    - Route optimization for resource delivery
    - Hotspot mapping and visualization
    - Distance and travel time calculations
    - Geographic clustering analysis
    """
    
    def __init__(self, api_key: str):
        self.gmaps = googlemaps.Client(key=api_key)
        self.logger = logging.getLogger(__name__)
        
    async def geocode_location(self, location: str) -> Dict:
        """
        Convert location string to geographic coordinates
        
        Args:
            location: Location string (e.g., "Los Angeles, CA")
            
        Returns:
            Dict with coordinates, formatted address, and metadata
        """
        try:
            geocode_result = self.gmaps.geocode(location)
            
            if not geocode_result:
                return {
                    "success": False,
                    "error": "Location not found",
                    "location_input": location
                }
            
            result = geocode_result[0]
            geometry = result['geometry']['location']
            
            return {
                "success": True,
                "location_input": location,
                "formatted_address": result['formatted_address'],
                "coordinates": {
                    "latitude": geometry['lat'],
                    "longitude": geometry['lng']
                },
                "place_id": result.get('place_id'),
                "address_components": result.get('address_components', []),
                "location_type": result['geometry'].get('location_type')
            }
            
        except Exception as e:
            self.logger.error(f"Geocoding error for {location}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "location_input": location
            }
    
    async def calculate_hotspot_routes(self, facilities: List[Dict], 
                                     hotspot_centers: List[Dict]) -> Dict:
        """
        Calculate optimal routes from facilities to outbreak hotspots
        
        Args:
            facilities: List of facility locations with coordinates
            hotspot_centers: List of outbreak hotspot coordinates
            
        Returns:
            Optimized routing plan with distances and travel times
        """
        try:
            routing_plan = {
                "optimization_timestamp": datetime.now().isoformat(),
                "facility_routes": [],
                "summary": {
                    "total_facilities": len(facilities),
                    "total_hotspots": len(hotspot_centers),
                    "optimization_method": "distance_and_time"
                }
            }
            
            for facility in facilities:
                facility_routes = await self._calculate_facility_routes(
                    facility, hotspot_centers
                )
                routing_plan["facility_routes"].append(facility_routes)
            
            return routing_plan
            
        except Exception as e:
            self.logger.error(f"Route calculation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_facility_routes(self, facility: Dict, 
                                       hotspots: List[Dict]) -> Dict:
        """Calculate routes from a facility to all hotspots"""
        
        facility_coord = facility.get("coordinates", {})
        facility_location = (facility_coord.get("latitude"), 
                           facility_coord.get("longitude"))
        
        routes = []
        
        for hotspot in hotspots:
            hotspot_coord = hotspot.get("coordinates", {})
            hotspot_location = (hotspot_coord.get("latitude"),
                              hotspot_coord.get("longitude"))
            
            # Calculate distance and duration
            try:
                directions = self.gmaps.directions(
                    facility_location,
                    hotspot_location,
                    mode="driving",
                    departure_time=datetime.now(),
                    traffic_model="best_guess"
                )
                
                if directions:
                    route = directions[0]
                    leg = route['legs'][0]
                    
                    route_info = {
                        "hotspot_id": hotspot.get("id", "unknown"),
                        "distance": {
                            "text": leg['distance']['text'],
                            "meters": leg['distance']['value']
                        },
                        "duration": {
                            "text": leg['duration']['text'],
                            "seconds": leg['duration']['value']
                        },
                        "duration_in_traffic": {
                            "text": leg.get('duration_in_traffic', {}).get('text', 'N/A'),
                            "seconds": leg.get('duration_in_traffic', {}).get('value', 0)
                        },
                        "start_address": leg['start_address'],
                        "end_address": leg['end_address'],
                        "route_quality": "optimal"
                    }
                    
                    routes.append(route_info)
                    
            except Exception as e:
                self.logger.warning(f"Route calculation failed for hotspot: {str(e)}")
                # Add fallback distance calculation
                routes.append({
                    "hotspot_id": hotspot.get("id", "unknown"),
                    "error": "Route calculation failed",
                    "fallback_distance": self._calculate_haversine_distance(
                        facility_location, hotspot_location
                    )
                })
        
        return {
            "facility_id": facility.get("id", "unknown"),
            "facility_name": facility.get("name", "Unknown Facility"),
            "facility_coordinates": facility_coord,
            "routes_to_hotspots": routes,
            "total_hotspots": len(routes)
        }
    
    def _calculate_haversine_distance(self, coord1: Tuple[float, float], 
                                    coord2: Tuple[float, float]) -> Dict:
        """Calculate approximate distance using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        distance_km = c * r
        
        return {
            "text": f"{distance_km:.2f} km",
            "meters": int(distance_km * 1000),
            "calculation_method": "haversine"
        }
    
    async def find_nearby_facilities(self, location: str, facility_type: str,
                                   radius: int = 10000) -> Dict:
        """
        Find nearby facilities of specified type
        
        Args:
            location: Center location for search
            facility_type: Type of facility (hospital, pharmacy, clinic)
            radius: Search radius in meters
            
        Returns:
            List of nearby facilities with details
        """
        try:
            geocode_result = await self.geocode_location(location)
            
            if not geocode_result.get("success"):
                return geocode_result
            
            coordinates = geocode_result["coordinates"]
            search_location = (coordinates["latitude"], coordinates["longitude"])
            
            # Map facility types to Google Places types
            place_types = {
                "hospital": "hospital",
                "clinic": "doctor",
                "pharmacy": "pharmacy",
                "testing_center": "hospital",
                "emergency": "hospital"
            }
            
            places_type = place_types.get(facility_type, "hospital")
            
            places_result = self.gmaps.places_nearby(
                location=search_location,
                radius=radius,
                type=places_type
            )
            
            facilities = []
            for place in places_result.get('results', []):
                facility_info = {
                    "place_id": place.get('place_id'),
                    "name": place.get('name'),
                    "type": facility_type,
                    "coordinates": {
                        "latitude": place['geometry']['location']['lat'],
                        "longitude": place['geometry']['location']['lng']
                    },
                    "address": place.get('vicinity'),
                    "rating": place.get('rating'),
                    "rating_count": place.get('user_ratings_total'),
                    "open_now": place.get('opening_hours', {}).get('open_now'),
                    "price_level": place.get('price_level')
                }
                
                facilities.append(facility_info)
            
            return {
                "success": True,
                "search_location": location,
                "facility_type": facility_type,
                "search_radius_meters": radius,
                "facilities_found": len(facilities),
                "facilities": facilities
            }
            
        except Exception as e:
            self.logger.error(f"Facility search error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_outbreak_heatmap_data(self, outbreak_data: List[Dict]) -> Dict:
        """
        Create heatmap data for outbreak visualization
        
        Args:
            outbreak_data: List of locations with case counts
            
        Returns:
            Heatmap data suitable for Google Maps visualization
        """
        try:
            heatmap_points = []
            
            for data_point in outbreak_data:
                location = data_point.get("location")
                case_count = data_point.get("case_count", 0)
                
                # Geocode location if coordinates not provided
                if "coordinates" not in data_point:
                    geocode_result = await self.geocode_location(location)
                    if geocode_result.get("success"):
                        coordinates = geocode_result["coordinates"]
                    else:
                        continue
                else:
                    coordinates = data_point["coordinates"]
                
                # Calculate weight based on case count
                weight = min(max(case_count / 100, 0.1), 10.0)  # Normalize to 0.1-10.0
                
                heatmap_point = {
                    "location": {
                        "lat": coordinates["latitude"],
                        "lng": coordinates["longitude"]
                    },
                    "weight": weight,
                    "case_count": case_count,
                    "location_name": location
                }
                
                heatmap_points.append(heatmap_point)
            
            return {
                "success": True,
                "heatmap_data": heatmap_points,
                "total_points": len(heatmap_points),
                "map_center": self._calculate_center_point(heatmap_points),
                "bounds": self._calculate_bounds(heatmap_points)
            }
            
        except Exception as e:
            self.logger.error(f"Heatmap creation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _calculate_center_point(self, points: List[Dict]) -> Dict:
        """Calculate geographic center of points"""
        if not points:
            return {"lat": 39.8283, "lng": -98.5795}  # Center of US
        
        total_lat = sum(point["location"]["lat"] for point in points)
        total_lng = sum(point["location"]["lng"] for point in points)
        
        return {
            "lat": total_lat / len(points),
            "lng": total_lng / len(points)
        }
    
    def _calculate_bounds(self, points: List[Dict]) -> Dict:
        """Calculate bounding box for points"""
        if not points:
            return {
                "north": 49.0, "south": 25.0,
                "east": -66.0, "west": -124.0
            }
        
        lats = [point["location"]["lat"] for point in points]
        lngs = [point["location"]["lng"] for point in points]
        
        return {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        }
    
    async def get_travel_matrix(self, origins: List[str], 
                              destinations: List[str]) -> Dict:
        """
        Get travel distance/time matrix between origins and destinations
        
        Args:
            origins: List of origin locations
            destinations: List of destination locations
            
        Returns:
            Matrix of distances and travel times
        """
        try:
            matrix = self.gmaps.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode="driving",
                departure_time=datetime.now()
            )
            
            return {
                "success": True,
                "origins": origins,
                "destinations": destinations,
                "matrix": matrix,
                "calculation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Distance matrix error: {str(e)}")
            return {"success": False, "error": str(e)}