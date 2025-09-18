from collections import defaultdict
from .osm_data import OSMDataFetcher, haversine
import logging
import math
from datetime import datetime, time
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class AreaAnalyzer:
    def __init__(self):
        self.osm_fetcher = OSMDataFetcher()

        self.building_factors = {
            'office': {'base': 2.2, 'capacity_multiplier': 0.1, 'peak_hours': [7, 8, 9, 17, 18, 19]},
            'commercial': {'base': 1.8, 'capacity_multiplier': 0.08, 'peak_hours': [10, 11, 12, 16, 17, 18, 19, 20]},
            'retail': {'base': 2.0, 'capacity_multiplier': 0.12, 'peak_hours': [10, 11, 12, 16, 17, 18, 19, 20, 21]},
            'industrial': {'base': 1.6, 'capacity_multiplier': 0.05, 'peak_hours': [6, 7, 8, 16, 17, 18]},
            'apartments': {'base': 1.5, 'capacity_multiplier': 0.03, 'peak_hours': [7, 8, 9, 17, 18, 19]},
            'school': {'base': 2.5, 'capacity_multiplier': 0.15, 'peak_hours': [7, 8, 13, 14, 15, 16]},
            'university': {'base': 2.2, 'capacity_multiplier': 0.12, 'peak_hours': [8, 9, 10, 16, 17, 18]},
            'hospital': {'base': 1.9, 'capacity_multiplier': 0.08, 'peak_hours': []},
            'shopping': {'base': 2.4, 'capacity_multiplier': 0.18, 'peak_hours': [10, 11, 12, 16, 17, 18, 19, 20]},
            'restaurant': {'base': 1.7, 'capacity_multiplier': 0.25, 'peak_hours': [12, 13, 19, 20, 21]},
            'public': {'base': 1.6, 'capacity_multiplier': 0.06, 'peak_hours': [9, 10, 11, 14, 15, 16]},
            'default': {'base': 1.0, 'capacity_multiplier': 0.02, 'peak_hours': []}
        }

        self.road_factors = {
            "Автомагістралі": {'congestion': 4.2, 'capacity': 2000, 'speed_factor': 1.0},
            "Головні": {'congestion': 3.8, 'capacity': 1500, 'speed_factor': 0.8},
            "Другорядні": {'congestion': 2.2, 'capacity': 800, 'speed_factor': 0.6},
            "Місцеві": {'congestion': 1.0, 'capacity': 400, 'speed_factor': 0.4},
            "Пішохідні": {'congestion': 0.1, 'capacity': 50, 'speed_factor': 0.1},
            "Велосипедні": {'congestion': 0.2, 'capacity': 100, 'speed_factor': 0.2}
        }

        self.area_time_patterns = {
            'business': {
                0: 0.2, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.2, 6: 0.4,
                7: 1.8, 8: 2.4, 9: 2.0, 10: 1.2, 11: 1.3, 12: 1.4,
                13: 1.3, 14: 1.2, 15: 1.4, 16: 1.8, 17: 2.5, 18: 2.3,
                19: 1.6, 20: 0.8, 21: 0.6, 22: 0.4, 23: 0.3
            },
            'residential': {
                0: 0.3, 1: 0.2, 2: 0.1, 3: 0.1, 4: 0.2, 5: 0.4, 6: 0.8,
                7: 1.6, 8: 1.9, 9: 1.2, 10: 0.8, 11: 0.9, 12: 1.1,
                13: 1.0, 14: 1.1, 15: 1.3, 16: 1.5, 17: 1.9, 18: 2.0,
                19: 1.4, 20: 1.0, 21: 0.8, 22: 0.6, 23: 0.4
            },
            'mixed': {
                0: 0.25, 1: 0.15, 2: 0.1, 3: 0.1, 4: 0.15, 5: 0.3, 6: 0.6,
                7: 1.7, 8: 2.1, 9: 1.6, 10: 1.0, 11: 1.1, 12: 1.25,
                13: 1.15, 14: 1.15, 15: 1.35, 16: 1.65, 17: 2.2, 18: 2.15,
                19: 1.5, 20: 0.9, 21: 0.7, 22: 0.5, 23: 0.35
            }
        }

    def perform_analysis(self, nw_lat: float, nw_lng: float, se_lat: float, se_lng: float) -> dict:
        north_bound = max(nw_lat, se_lat)
        south_bound = min(nw_lat, se_lat)
        east_bound = max(nw_lng, se_lng)
        west_bound = min(nw_lng, se_lng)

        osm_data = self.osm_fetcher.get_area_data(north_bound, west_bound, south_bound, east_bound)
        area_size = self._calculate_area_size(north_bound, west_bound, south_bound, east_bound)

        roads, road_count, road_types = self._extract_road_data(osm_data)
        intersections = self._analyze_intersections(roads, osm_data)
        traffic_lights = self._count_traffic_infrastructure(osm_data)
        parking_data = self._analyze_parking(osm_data)
        buildings = self._extract_building_data(osm_data)
        green_spaces, water_features = self._extract_green_and_water_data(osm_data)
        public_transport = self._analyze_public_transport(osm_data)

        area_type = self._determine_area_type(buildings, road_types)

        base_congestion = self._calculate_base_congestion(road_types, roads, intersections, traffic_lights)
        building_impact = self._calculate_advanced_building_impact(buildings, roads, osm_data)
        parking_impact = self._calculate_parking_impact(parking_data, roads)
        transport_relief = self._calculate_transport_relief(public_transport)

        congestion_level = self._calculate_final_congestion(
            base_congestion, building_impact, parking_impact, transport_relief
        )

        hourly_congestion = self._calculate_advanced_hourly_congestion(
            area_type, base_congestion, building_impact, buildings
        )

        ecology_score = self._calculate_ecology_score(
            green_spaces, water_features, area_size, roads, road_types,
            traffic_lights, parking_data, hourly_congestion
        )

        return {
            "bounds": [[north_bound, west_bound], [south_bound, east_bound]],
            "area": round(area_size, 2),
            "area_type": area_type,
            "road_count": road_count,
            "road_types": dict(road_types),
            "intersections": intersections,
            "traffic_lights": traffic_lights,
            "parking_spots": parking_data['total_spots'],
            "longest_road": self._find_longest_road(roads),
            "congestion": congestion_level,
            "congestion_details": {
                "base_road_congestion": round(base_congestion, 1),
                "building_impact": round(building_impact, 1),
                "parking_impact": round(parking_impact, 1),
                "transport_relief": round(-transport_relief, 1)
            },
            "ecology": ecology_score,
            "pedestrian_friendly": self._calculate_pedestrian_score(roads, road_types),
            "public_transport": self._calculate_transport_score(public_transport),
            "hourly_congestion": hourly_congestion,
            "roads_data": roads,
            "green_spaces_data": green_spaces,
            "water_features_data": water_features,
            "buildings_data": buildings,
            "parking_data": parking_data
        }

    def _calculate_area_size(self, north: float, west: float, south: float, east: float) -> float:
        try:
            avg_latitude = (north + south) / 2
            width_km = haversine(west, avg_latitude, east, avg_latitude)
            height_km = haversine(west, north, west, south)
            return round(width_km * height_km, 2)
        except Exception as e:
            logger.error(f"Помилка при обчисленні площі: {e}")
            return 1.0

    def _extract_road_data(self, osm_data: dict) -> Tuple[List[dict], int, defaultdict]:
        roads = []
        road_count = 0
        road_type_counts = defaultdict(int)

        nodes = {
            element["id"]: (element["lat"], element["lon"])
            for element in osm_data.get("elements", [])
            if element["type"] == "node"
        }

        for element in osm_data.get("elements", []):
            if element["type"] == "way" and "highway" in element.get("tags", {}):
                highway_type = element["tags"]["highway"]
                tags = element.get("tags", {})

                road_length = self._calculate_road_length(element, nodes)
                lanes = self._extract_lane_count(tags)
                max_speed = self._extract_max_speed(tags)

                roads.append({
                    "id": element["id"],
                    "type": highway_type,
                    "name": tags.get("name", "Unnamed road"),
                    "length": round(road_length, 2),
                    "lanes": lanes,
                    "max_speed": max_speed,
                    "nodes": element.get("nodes", []),
                    "surface": tags.get("surface", "unknown"),
                    "oneway": tags.get("oneway", "no") == "yes"
                })

                self._categorize_road_advanced(road_type_counts, highway_type, tags)
                road_count += 1

        return roads, road_count, road_type_counts

    def _extract_max_speed(self, tags: dict) -> Optional[int]:
        max_speed = tags.get('maxspeed')
        if max_speed:
            try:
                speed_str = str(max_speed).split()[0]
                return int(speed_str)
            except (ValueError, IndexError):
                pass
        return None

    def _categorize_road_advanced(self, road_types: dict, highway_type: str, tags: dict):
        mapping = {
            "Автомагістралі": ["motorway", "motorway_link"],
            "Головні": ["trunk", "trunk_link", "primary", "primary_link"],
            "Другорядні": ["secondary", "secondary_link", "tertiary", "tertiary_link"],
            "Місцеві": ["residential", "service", "unclassified", "living_street"],
            "Пішохідні": ["pedestrian", "footway", "path", "steps", "walkway"],
            "Велосипедні": ["cycleway"]
        }

        for category, types in mapping.items():
            if highway_type in types or (category == "Велосипедні" and tags.get("bicycle") == "designated"):
                road_types[category] += 1
                break

    def _analyze_intersections(self, roads: List[dict], osm_data: dict) -> dict:
        nodes = {
            element["id"]: (element["lat"], element["lon"])
            for element in osm_data.get("elements", [])
            if element["type"] == "node"
        }

        node_connections = defaultdict(list)
        for road in roads:
            for node_id in road.get("nodes", []):
                if node_id in nodes:
                    node_connections[node_id].append(road)

        intersections = {
            "simple": 0,
            "complex": 0,
            "major": 0,
            "total": 0
        }

        for node_id, connected_roads in node_connections.items():
            road_count = len(connected_roads)

            if road_count >= 3:
                intersections["total"] += 1

                has_major_road = any(
                    road["type"] in ["motorway", "trunk", "primary"]
                    for road in connected_roads
                )

                if road_count >= 5 or has_major_road:
                    intersections["major"] += 1
                elif road_count == 4:
                    intersections["complex"] += 1
                else:
                    intersections["simple"] += 1

        return intersections

    def _count_traffic_infrastructure(self, osm_data: dict) -> dict:
        infrastructure = {
            "traffic_lights": 0,
            "stop_signs": 0,
            "speed_cameras": 0,
            "roundabouts": 0
        }

        for element in osm_data.get("elements", []):
            if element["type"] == "node" and "tags" in element:
                tags = element["tags"]

                if tags.get("highway") == "traffic_signals":
                    infrastructure["traffic_lights"] += 1
                elif tags.get("highway") == "stop":
                    infrastructure["stop_signs"] += 1
                elif tags.get("highway") == "speed_camera":
                    infrastructure["speed_cameras"] += 1

            elif element["type"] == "way" and "tags" in element:
                if element["tags"].get("junction") == "roundabout":
                    infrastructure["roundabouts"] += 1

        return infrastructure

    def _analyze_parking(self, osm_data: dict) -> dict:
        parking_data = {
            "total_spots": 0,
            "surface_parking": 0,
            "underground_parking": 0,
            "street_parking": 0,
            "parking_lots": 0
        }

        for element in osm_data.get("elements", []):
            if "tags" not in element:
                continue

            tags = element["tags"]

            if tags.get("amenity") == "parking":
                parking_data["parking_lots"] += 1

                capacity = tags.get("capacity")
                if capacity:
                    try:
                        spots = int(capacity)
                        parking_data["total_spots"] += spots
                    except ValueError:
                        parking_data["total_spots"] += 20
                else:
                    parking_data["total_spots"] += 20

                parking_type = tags.get("parking", "surface")
                if parking_type == "underground":
                    parking_data["underground_parking"] += 1
                else:
                    parking_data["surface_parking"] += 1

            elif tags.get("highway") and tags.get("parking:lane"):
                parking_data["street_parking"] += 1
                parking_data["total_spots"] += 5

        return parking_data

    def _determine_area_type(self, buildings: List[dict], road_types: defaultdict) -> str:
        if not buildings:
            return 'mixed'

        building_types = defaultdict(int)
        for building in buildings:
            building_type = building.get('type', 'unknown').lower()

            if any(t in building_type for t in ['office', 'commercial', 'retail']):
                building_types['commercial'] += 1
            elif any(t in building_type for t in ['apartment', 'residential', 'house']):
                building_types['residential'] += 1
            elif any(t in building_type for t in ['school', 'university', 'hospital']):
                building_types['institutional'] += 1
            elif any(t in building_type for t in ['industrial', 'warehouse']):
                building_types['industrial'] += 1

        total_buildings = sum(building_types.values())
        if total_buildings == 0:
            return 'mixed'

        max_type = max(building_types.items(), key=lambda x: x[1])

        if max_type[1] / total_buildings > 0.6:
            if max_type[0] == 'commercial':
                return 'business'
            elif max_type[0] == 'residential':
                return 'residential'
            else:
                return 'mixed'
        else:
            return 'mixed'

    def _calculate_base_congestion(self, road_types: defaultdict, roads: List[dict],
                                   intersections: dict, traffic_lights: dict) -> float:
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 20.0

        road_congestion = 0
        total_capacity = 0

        for road_type, count in road_types.items():
            if road_type in self.road_factors:
                factor_data = self.road_factors[road_type]
                road_congestion += count * factor_data['congestion']
                total_capacity += count * factor_data['capacity']

        max_possible_congestion = total_roads * max(
            factor['congestion'] for factor in self.road_factors.values()
        )
        base_level = (road_congestion / max_possible_congestion) * 60 if max_possible_congestion > 0 else 20

        intersection_impact = (
                intersections['simple'] * 0.5 +
                intersections['complex'] * 1.2 +
                intersections['major'] * 2.5
        )
        intersection_factor = min(15, intersection_impact / max(total_roads, 1) * 100)

        traffic_light_factor = min(10, traffic_lights['traffic_lights'] / max(total_roads, 1) * 50)

        return min(85, base_level + intersection_factor + traffic_light_factor)

    def _calculate_advanced_building_impact(self, buildings: List[dict], roads: List[dict],
                                            osm_data: dict) -> float:
        if not buildings or not roads:
            return 0.0

        node_coords = {
            element["id"]: (element["lat"], element["lon"])
            for element in osm_data.get("elements", [])
            if element["type"] == "node"
        }

        total_impact = 0.0
        building_count = 0

        for building in buildings:
            if not building.get('nodes'):
                continue

            building_center = self._get_building_center(building, node_coords)
            if not building_center:
                continue

            nearest_road_distance = self._find_nearest_road_distance(building_center, roads, node_coords)
            if nearest_road_distance == float('inf'):
                continue

            building_type = self._normalize_building_type(building['type'])
            factor_data = self.building_factors.get(building_type, self.building_factors['default'])

            building_capacity = self._estimate_building_capacity(building, node_coords)

            base_impact = factor_data['base']
            capacity_impact = building_capacity * factor_data['capacity_multiplier']
            distance_factor = 1.0 / max(0.05, min(nearest_road_distance, 1.0))

            building_impact = (base_impact + capacity_impact) * distance_factor
            total_impact += building_impact
            building_count += 1

        return total_impact / max(building_count, 1)

    def _get_building_center(self, building: dict, node_coords: dict) -> Optional[Tuple[float, float]]:
        building_nodes = building.get('nodes', [])
        if not building_nodes:
            return None

        valid_coords = []
        for node_id in building_nodes:
            if node_id in node_coords:
                valid_coords.append(node_coords[node_id])

        if not valid_coords:
            return None

        avg_lat = sum(coord[0] for coord in valid_coords) / len(valid_coords)
        avg_lon = sum(coord[1] for coord in valid_coords) / len(valid_coords)
        return (avg_lat, avg_lon)

    def _find_nearest_road_distance(self, building_center: Tuple[float, float],
                                    roads: List[dict], node_coords: dict) -> float:
        min_distance = float('inf')

        for road in roads:
            for node_id in road.get('nodes', []):
                if node_id in node_coords:
                    road_coords = node_coords[node_id]
                    distance = haversine(
                        building_center[1], building_center[0],
                        road_coords[1], road_coords[0]
                    )
                    min_distance = min(min_distance, distance)

        return min_distance

    def _normalize_building_type(self, building_type: str) -> str:
        building_type = building_type.lower()

        type_mapping = {
            'office': ['office', 'commercial'],
            'retail': ['retail', 'shop', 'mall', 'supermarket'],
            'school': ['school', 'kindergarten'],
            'university': ['university', 'college'],
            'hospital': ['hospital', 'clinic', 'medical'],
            'industrial': ['industrial', 'warehouse', 'factory'],
            'apartments': ['apartments', 'residential'],
            'restaurant': ['restaurant', 'cafe', 'fast_food'],
            'shopping': ['shopping', 'department_store']
        }

        for category, keywords in type_mapping.items():
            if any(keyword in building_type for keyword in keywords):
                return category

        return 'default'

    def _estimate_building_capacity(self, building: dict, node_coords: dict) -> float:
        tags = building.get('tags', {})

        levels = 1
        if 'building:levels' in tags:
            try:
                levels = int(tags['building:levels'])
            except (ValueError, TypeError):
                levels = 1

        area_factor = len(building.get('nodes', [])) / 4.0

        return levels * area_factor

    def _calculate_parking_impact(self, parking_data: dict, roads: List[dict]) -> float:
        if not roads:
            return 0.0

        total_roads = len(roads)
        parking_spots = parking_data['total_spots']
        road_length_total = sum(road.get('length', 0) for road in roads)

        if road_length_total == 0:
            return 0.0

        expected_spots = road_length_total * 50
        spot_deficit = max(0, expected_spots - parking_spots)

        street_parking_impact = parking_data['street_parking'] * 0.3

        deficit_impact = (spot_deficit / expected_spots) * 15 if expected_spots > 0 else 0

        return min(20, deficit_impact + street_parking_impact)

    def _analyze_public_transport(self, osm_data: dict) -> dict:
        transport_data = {
            'bus_stops': 0,
            'tram_stops': 0,
            'metro_stations': 0,
            'train_stations': 0,
            'total_stops': 0
        }

        for element in osm_data.get("elements", []):
            if element["type"] == "node" and "tags" in element:
                tags = element["tags"]

                if tags.get("highway") == "bus_stop" or tags.get("public_transport") == "stop_position":
                    transport_data['bus_stops'] += 1
                elif tags.get("railway") == "tram_stop":
                    transport_data['tram_stops'] += 1
                elif tags.get("railway") == "station":
                    if tags.get("station") == "subway":
                        transport_data['metro_stations'] += 1
                    else:
                        transport_data['train_stations'] += 1

        transport_data['total_stops'] = sum([
            transport_data['bus_stops'],
            transport_data['tram_stops'],
            transport_data['metro_stations'],
            transport_data['train_stations']
        ])

        return transport_data

    def _calculate_transport_relief(self, transport_data: dict) -> float:
        relief_factors = {
            'bus_stops': 0.8,
            'tram_stops': 1.5,
            'metro_stations': 3.0,
            'train_stations': 2.0
        }

        total_relief = 0
        for transport_type, count in transport_data.items():
            if transport_type in relief_factors:
                total_relief += count * relief_factors[transport_type]

        return min(25, total_relief)

    def _calculate_final_congestion(self, base_congestion: float, building_impact: float,
                                    parking_impact: float, transport_relief: float) -> int:
        total_congestion = base_congestion + building_impact + parking_impact - transport_relief
        return min(95, max(5, int(total_congestion)))

    def _calculate_advanced_hourly_congestion(self, area_type: str, base_congestion: float,
                                              building_impact: float, buildings: List[dict]) -> List[int]:
        if area_type not in self.area_time_patterns:
            area_type = 'mixed'

        time_pattern = self.area_time_patterns[area_type]
        hourly_congestion = []

        building_type_counts = defaultdict(int)
        for building in buildings:
            normalized_type = self._normalize_building_type(building.get('type', ''))
            building_type_counts[normalized_type] += 1

        for hour in range(24):
            time_factor = time_pattern[hour]

            building_time_adjustment = self._calculate_building_time_adjustment(
                hour, building_type_counts
            )

            combined_time_factor = time_factor * (1 + building_time_adjustment)

            hourly_level = (base_congestion + building_impact) * combined_time_factor

            if hour in [7, 8, 17, 18]:
                hourly_level *= 1.1
            elif 22 <= hour or hour <= 5:
                hourly_level *= 0.7

            hourly_congestion.append(min(95, max(5, int(hourly_level))))

        return hourly_congestion

    def _calculate_building_time_adjustment(self, hour: int, building_counts: defaultdict) -> float:
        adjustment = 0.0
        total_buildings = sum(building_counts.values())

        if total_buildings == 0:
            return 0.0

        for building_type, count in building_counts.items():
            if building_type in self.building_factors:
                peak_hours = self.building_factors[building_type]['peak_hours']

                if not peak_hours:
                    continue

                if hour in peak_hours:
                    weight = count / total_buildings
                    adjustment += weight * 0.3

        return min(0.5, adjustment)

    def _extract_lane_count(self, tags: dict) -> int:
        lanes = tags.get('lanes', '2')
        try:
            if isinstance(lanes, str):
                if '-' in lanes:
                    lane_values = [int(x.strip()) for x in lanes.split('-')]
                    return sum(lane_values) // len(lane_values)
                elif ';' in lanes:
                    lane_values = [int(x.strip()) for x in lanes.split(';')]
                    return max(lane_values)
                return int(lanes)
            return int(lanes)
        except (ValueError, TypeError):
            highway_type = tags.get('highway', '')
            if highway_type in ['motorway', 'trunk']:
                return 3
            elif highway_type in ['primary', 'secondary']:
                return 2
            else:
                return 1

    def _calculate_road_length(self, road_element: dict, nodes: dict) -> float:
        length = 0.0
        road_nodes = road_element.get("nodes", [])

        if len(road_nodes) > 1:
            for i in range(len(road_nodes) - 1):
                node1, node2 = road_nodes[i], road_nodes[i + 1]
                if node1 in nodes and node2 in nodes:
                    lat1, lon1 = nodes[node1]
                    lat2, lon2 = nodes[node2]
                    segment_length = haversine(lon1, lat1, lon2, lat2)
                    length += segment_length
        return length

    def _extract_green_and_water_data(self, osm_data: dict) -> Tuple[List[dict], List[dict]]:
        green_spaces = []
        water_features = []

        for element in osm_data.get("elements", []):
            if element["type"] not in ["way", "relation"] or "tags" not in element:
                continue

            tags = element["tags"]

            if (tags.get("leisure") in ["park", "garden", "nature_reserve"] or
                    tags.get("natural") in ["wood", "forest", "scrub"] or
                    tags.get("landuse") in ["forest", "meadow", "grass", "recreation_ground"]):
                green_spaces.append({
                    "id": element["id"],
                    "type": tags.get("leisure") or tags.get("natural") or tags.get("landuse"),
                    "name": tags.get("name", "Unnamed green space"),
                    "area": self._estimate_polygon_area(element, osm_data)
                })

            if (tags.get("natural") in ["water", "coastline"] or
                    tags.get("waterway") in ["river", "stream", "canal"]):
                water_features.append({
                    "id": element["id"],
                    "type": tags.get("waterway") or tags.get("natural"),
                    "name": tags.get("name", "Unnamed water feature"),
                    "area": self._estimate_polygon_area(element, osm_data)
                })

        return green_spaces, water_features

    def _extract_building_data(self, osm_data: dict) -> List[dict]:
        buildings = []

        for element in osm_data.get("elements", []):
            if element["type"] not in ["way", "relation"] or "tags" not in element:
                continue

            tags = element["tags"]

            if "building" in tags:
                building_type = (
                        tags.get("amenity") or
                        tags.get("building:use") or
                        tags.get("shop") or
                        tags.get("office") or
                        tags.get("building") or
                        "unknown"
                )

                building_data = {
                    "id": element["id"],
                    "type": building_type,
                    "name": tags.get("name", "Unnamed building"),
                    "nodes": element.get("nodes", []),
                    "levels": tags.get("building:levels"),
                    "height": tags.get("height"),
                    "capacity": tags.get("capacity"),
                    "area": self._estimate_polygon_area(element, osm_data)
                }

                buildings.append(building_data)

        return buildings

    def _estimate_polygon_area(self, element: dict, osm_data: dict) -> Optional[float]:
        if element["type"] != "way":
            return None

        nodes = {
            e["id"]: (e["lat"], e["lon"])
            for e in osm_data.get("elements", [])
            if e["type"] == "node"
        }

        element_nodes = element.get("nodes", [])
        if len(element_nodes) < 3:
            return None

        coords = []
        for node_id in element_nodes:
            if node_id in nodes:
                coords.append(nodes[node_id])

        if len(coords) < 3:
            return None

        area = 0.0
        for i in range(len(coords)):
            j = (i + 1) % len(coords)
            area += coords[i][0] * coords[j][1]
            area -= coords[j][0] * coords[i][1]

        area = abs(area) / 2.0
        area_km2 = area * 111.32 * 111.32 * 0.001
        return area_km2

    def _find_longest_road(self, roads: List[dict]) -> dict:
        if not roads:
            return {"name": "No data", "length": 0, "type": "unknown"}

        named_roads = [road for road in roads if road.get("name") != "Unnamed road"]

        if named_roads:
            longest = max(named_roads, key=lambda x: x.get("length", 0))
        else:
            longest = max(roads, key=lambda x: x.get("length", 0))

        return {
            "name": longest.get("name", "Unnamed road"),
            "length": longest.get("length", 0),
            "type": longest.get("type", "unknown"),
            "lanes": longest.get("lanes", 1)
        }

    def _calculate_ecology_score(self, green_spaces: List[dict], water_features: List[dict],
                                 area: float, roads: List[dict], road_types: defaultdict,
                                 traffic_lights: dict, parking_data: dict,
                                 hourly_congestion: List[int]) -> dict:
        if area <= 0:
            area = 1.0

        green_score = self._calculate_green_coverage_score(green_spaces, water_features, area)

        transport_impact = self._calculate_transport_environmental_impact(
            roads, road_types, traffic_lights, parking_data, hourly_congestion, area
        )

        air_quality_score = self._calculate_air_quality_score(
            road_types, hourly_congestion, green_spaces, area
        )

        noise_score = self._calculate_noise_pollution_score(
            roads, road_types, traffic_lights, area
        )

        total_ecology_score = (
                green_score * 0.40 +
                (100 - transport_impact) * 0.35 +
                air_quality_score * 0.15 +
                noise_score * 0.10
        )

        final_score = min(95, max(5, int(total_ecology_score)))

        return final_score

    def _calculate_green_coverage_score(self, green_spaces: List[dict],
                                        water_features: List[dict], area: float) -> float:
        green_area = sum(space.get('area', 0) for space in green_spaces if space.get('area'))
        water_area = sum(feature.get('area', 0) for feature in water_features if feature.get('area'))

        if green_area == 0 and green_spaces:
            green_area = len(green_spaces) * 0.01

        if water_area == 0 and water_features:
            water_area = len(water_features) * 0.005

        total_green_area = green_area + water_area * 1.2
        coverage_percent = (total_green_area / area) * 100

        green_types = set()
        for space in green_spaces:
            space_type = space.get('type', '').lower()
            if 'park' in space_type:
                green_types.add('park')
            elif 'forest' in space_type or 'wood' in space_type:
                green_types.add('forest')
            elif 'garden' in space_type:
                green_types.add('garden')
            else:
                green_types.add('other')

        diversity_bonus = min(10, len(green_types) * 3)

        if coverage_percent >= 50:
            base_score = 90
        elif coverage_percent >= 30:
            base_score = 70 + (coverage_percent - 30) * 1.0
        elif coverage_percent >= 15:
            base_score = 50 + (coverage_percent - 15) * 1.33
        elif coverage_percent >= 5:
            base_score = 30 + (coverage_percent - 5) * 2.0
        else:
            base_score = coverage_percent * 6

        total_score = base_score + diversity_bonus
        return min(95, max(10, total_score))

    def _calculate_transport_environmental_impact(self, roads: List[dict], road_types: defaultdict,
                                                  traffic_lights: dict, parking_data: dict,
                                                  hourly_congestion: List[int], area: float) -> float:

        avg_congestion = sum(hourly_congestion) / len(hourly_congestion) if hourly_congestion else 30
        congestion_impact = avg_congestion * 0.8

        road_impact = 0
        total_road_length = sum(road.get('length', 0) for road in roads)

        if total_road_length > 0:
            for road_type, count in road_types.items():
                type_length = sum(road.get('length', 0) for road in roads
                                  if self._get_road_category(road.get('type', '')) == road_type)

                if type_length > 0:
                    length_ratio = type_length / total_road_length

                    road_pollution_factors = {
                        "Автомагістралі": 4.5,
                        "Головні": 3.5,
                        "Другорядні": 2.0,
                        "Місцеві": 1.0,
                        "Пішохідні": 0.1,
                        "Велосипедні": 0.2
                    }

                    factor = road_pollution_factors.get(road_type, 2.0)
                    road_impact += length_ratio * factor * 20

        parking_impact = 0
        if parking_data.get('total_spots', 0) > 0:
            parking_density = parking_data['total_spots'] / area
            parking_impact = min(20, parking_density * 0.01)

        traffic_light_impact = min(10, traffic_lights.get('traffic_lights', 0) / area * 5)

        estimated_vehicles = self._estimate_daily_vehicle_count(roads, hourly_congestion)
        vehicle_density = estimated_vehicles / area if area > 0 else 0
        vehicle_impact = min(25, vehicle_density * 0.001)

        total_impact = (congestion_impact + road_impact + parking_impact +
                        traffic_light_impact + vehicle_impact)

        return min(95, max(5, total_impact))

    def _calculate_air_quality_score(self, road_types: defaultdict, hourly_congestion: List[int],
                                     green_spaces: List[dict], area: float) -> float:

        avg_congestion = sum(hourly_congestion) / len(hourly_congestion) if hourly_congestion else 30
        base_air_quality = max(20, 100 - avg_congestion * 1.2)

        green_area = sum(space.get('area', 0) for space in green_spaces if space.get('area'))
        if green_area == 0 and green_spaces:
            green_area = len(green_spaces) * 0.01

        green_coverage = (green_area / area) * 100 if area > 0 else 0
        green_bonus = min(20, green_coverage * 0.6)

        major_roads = road_types.get("Автомагістралі", 0) + road_types.get("Головні", 0)
        total_roads = sum(road_types.values())
        major_road_penalty = 0
        if total_roads > 0:
            major_road_ratio = major_roads / total_roads
            major_road_penalty = major_road_ratio * 15

        final_score = base_air_quality + green_bonus - major_road_penalty
        return min(95, max(10, final_score))

    def _calculate_noise_pollution_score(self, roads: List[dict], road_types: defaultdict,
                                         traffic_lights: dict, area: float) -> float:

        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 80

        noise_level = 0
        for road_type, count in road_types.items():
            noise_factors = {
                "Автомагістралі": 4.0,
                "Головні": 3.0,
                "Другорядні": 2.0,
                "Місцеві": 1.0,
                "Пішохідні": 0.1,
                "Велосипедні": 0.2
            }

            factor = noise_factors.get(road_type, 1.5)
            road_ratio = count / total_roads
            noise_level += road_ratio * factor * 20

        traffic_light_noise = min(10, traffic_lights.get('traffic_lights', 0) / area * 3)

        total_noise = noise_level + traffic_light_noise

        noise_score = max(10, 100 - total_noise)
        return min(95, noise_score)

    def _estimate_daily_vehicle_count(self, roads: List[dict], hourly_congestion: List[int]) -> int:

        if not roads or not hourly_congestion:
            return 0

        total_vehicle_capacity = 0

        for road in roads:
            road_length = road.get('length', 0)
            lanes = road.get('lanes', 1)
            road_type = road.get('type', 'residential')

            traffic_intensity = {
                'motorway': 1500,
                'trunk': 1200,
                'primary': 800,
                'secondary': 500,
                'tertiary': 300,
                'residential': 150,
                'service': 100
            }

            base_intensity = traffic_intensity.get(road_type, 200)
            daily_vehicles = road_length * lanes * base_intensity
            total_vehicle_capacity += daily_vehicles

        avg_congestion = sum(hourly_congestion) / len(hourly_congestion)
        congestion_multiplier = 0.3 + (avg_congestion / 100) * 1.4  # 0.3 - 1.7

        estimated_vehicles = int(total_vehicle_capacity * congestion_multiplier)
        return max(0, estimated_vehicles)

    def _count_pollution_sources(self, road_types: defaultdict, parking_data: dict) -> dict:
        return {
            'major_roads': road_types.get("Автомагістралі", 0) + road_types.get("Головні", 0),
            'parking_lots': parking_data.get('parking_lots', 0),
            'total_parking_spots': parking_data.get('total_spots', 0)
        }

    def _get_green_coverage_percent(self, green_spaces: List[dict],
                                    water_features: List[dict], area: float) -> float:
        green_area = sum(space.get('area', 0) for space in green_spaces if space.get('area'))
        water_area = sum(feature.get('area', 0) for feature in water_features if feature.get('area'))

        if green_area == 0 and green_spaces:
            green_area = len(green_spaces) * 0.01
        if water_area == 0 and water_features:
            water_area = len(water_features) * 0.005

        total_green = green_area + water_area
        return round((total_green / area) * 100, 2) if area > 0 else 0

    def _get_road_category(self, highway_type: str) -> str:
        mapping = {
            "Автомагістралі": ["motorway", "motorway_link"],
            "Головні": ["trunk", "trunk_link", "primary", "primary_link"],
            "Другорядні": ["secondary", "secondary_link", "tertiary", "tertiary_link"],
            "Місцеві": ["residential", "service", "unclassified", "living_street"],
            "Пішохідні": ["pedestrian", "footway", "path", "steps", "walkway"],
            "Велосипедні": ["cycleway"]
        }

    def _calculate_pedestrian_score(self, roads: List[dict], road_types: defaultdict) -> int:
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 50

        pedestrian_roads = road_types.get("Пішохідні", 0)
        bicycle_roads = road_types.get("Велосипедні", 0)
        local_roads = road_types.get("Місцеві", 0)

        pedestrian_percentage = (pedestrian_roads / total_roads) * 100
        bicycle_percentage = (bicycle_roads / total_roads) * 100
        local_percentage = (local_roads / total_roads) * 100

        score = (
                pedestrian_percentage * 3 +
                bicycle_percentage * 2 +
                local_percentage * 0.5
        )

        return min(95, max(10, int(score)))

    def _calculate_transport_score(self, transport_data: dict) -> int:
        weights = {
            'bus_stops': 1.0,
            'tram_stops': 1.5,
            'metro_stations': 3.0,
            'train_stations': 2.0
        }

        weighted_score = 0
        for transport_type, count in transport_data.items():
            if transport_type in weights:
                weighted_score += count * weights[transport_type]

        score = min(95, max(10, int(weighted_score * 5)))
        return score