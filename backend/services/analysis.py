from collections import defaultdict
from math import radians, cos, sin, asin, sqrt
from .osm_data import OSMDataFetcher, haversine
import logging

logger = logging.getLogger(__name__)


class AreaAnalyzer:
    def __init__(self):
        self.osm_fetcher = OSMDataFetcher()

    def perform_analysis(self, nw_lat: float, nw_lng: float, se_lat: float, se_lng: float) -> dict:
        north_bound = max(nw_lat, se_lat)
        south_bound = min(nw_lat, se_lat)
        east_bound = max(nw_lng, se_lng)
        west_bound = min(nw_lng, se_lng)

        osm_data = self.osm_fetcher.get_area_data(north_bound, west_bound, south_bound, east_bound)
        area_size = self._calculate_area_size(north_bound, west_bound, south_bound, east_bound)

        roads, road_count, road_types = self._extract_road_data(osm_data)
        green_spaces, water_features = self._extract_green_and_water_data(osm_data)
        hourly_congestion = self._estimate_hourly_congestion(road_types)

        return {
            "bounds": [[north_bound, west_bound], [south_bound, east_bound]],
            "area": round(area_size, 2),
            "road_count": road_count,
            "road_types": dict(road_types),
            "longest_road": self._find_longest_road(roads),
            "congestion": self._calculate_congestion_level(road_types),
            "ecology": self._calculate_ecology_score(green_spaces, water_features, area_size),
            "pedestrian_friendly": self._calculate_pedestrian_score(roads, road_types),
            "public_transport": self._calculate_transport_score(osm_data),
            "hourly_congestion": hourly_congestion,
            "roads_data": roads,
            "green_spaces_data": green_spaces,
            "water_features_data": water_features
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

    def _extract_road_data(self, osm_data: dict) -> tuple:
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
                road_length = self._calculate_road_length(element, nodes)

                roads.append({
                    "id": element["id"],
                    "type": highway_type,
                    "name": element["tags"].get("name", "Unnamed road"),
                    "length": round(road_length, 2)
                })

                self._categorize_road(road_type_counts, highway_type, element.get("tags", {}))
                road_count += 1

        return roads, road_count, road_type_counts

    def _calculate_road_length(self, road_element: dict, nodes: dict) -> float:
        length = 0.0
        road_nodes = road_element.get("nodes", [])

        if len(road_nodes) > 1:
            for i in range(len(road_nodes) - 1):
                node1, node2 = road_nodes[i], road_nodes[i + 1]
                if node1 in nodes and node2 in nodes:
                    lat1, lon1 = nodes[node1]
                    lat2, lon2 = nodes[node2]
                    length += haversine(lon1, lat1, lon2, lat2)
        return length

    def _categorize_road(self, road_types: dict, highway_type: str, tags: dict):
        mapping = {
            "Головні": ["motorway", "trunk", "primary"],
            "Другорядні": ["secondary", "tertiary"],
            "Місцеві": ["residential", "service", "unclassified"],
            "Пішохідні": ["pedestrian", "footway", "path", "steps"],
            "Велосипедні": ["cycleway"]
        }
        for category, types in mapping.items():
            if highway_type in types or (category == "Велосипедні" and tags.get("bicycle") == "designated"):
                road_types[category] += 1
                break

    def _extract_green_and_water_data(self, osm_data: dict) -> tuple:
        green_spaces = []
        water_features = []

        for element in osm_data.get("elements", []):
            if element["type"] not in ["way", "relation"] or "tags" not in element:
                continue

            tags = element["tags"]

            if (tags.get("leisure") == "park"
                    or tags.get("natural") == "wood"
                    or tags.get("landuse") in ["forest", "meadow", "grass"]):
                green_spaces.append({
                    "id": element["id"],
                    "type": tags.get("leisure") or tags.get("natural") or tags.get("landuse"),
                    "name": tags.get("name", "Unnamed green space")
                })

            if tags.get("natural") == "water" or "waterway" in tags:
                water_features.append({
                    "id": element["id"],
                    "type": tags.get("waterway") or tags.get("natural"),
                    "name": tags.get("name", "Unnamed water feature")
                })

        return green_spaces, water_features

    def _calculate_score(self, value: float, max_value: float, weight: float = 1) -> int:
        return min(95, max(10, int(value * weight / max(max_value, 0.1))))

    def _calculate_ecology_score(self, green_spaces: list, water_features: list, area: float) -> int:
        green_score = self._calculate_score(len(green_spaces), area, 10)
        water_score = self._calculate_score(len(water_features), area, 15)
        return int(0.7 * green_score + 0.3 * water_score)

    def _calculate_pedestrian_score(self, roads: list, road_types: dict) -> int:
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 50
        return self._calculate_score(road_types.get("Пішохідні", 0), total_roads, 300)

    def _calculate_transport_score(self, osm_data: dict) -> int:
        keywords = [
            ("public_transport", ["stop_position", "platform"]),
            ("highway", ["bus_stop"]),
            ("railway", ["station", "halt", "tram_stop"])
        ]

        transport_stops = sum(
            1 for e in osm_data.get("elements", []) if e["type"] == "node" and "tags" in e and
            any(e["tags"].get(k) in v for k, v in keywords)
        )
        return self._calculate_score(transport_stops, 1, 5)

    def _calculate_congestion_level(self, road_types: dict) -> int:
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 50
        return self._calculate_score(road_types.get("Головні", 0), total_roads, 150)

    def _estimate_hourly_congestion(self, road_types: dict) -> list:
        main_road_weight = road_types.get("Головні", 0)
        secondary_road_weight = road_types.get("Другорядні", 0)
        local_roads = road_types.get("Місцеві", 0)

        total_weight = max(sum(road_types.values()), 1)
        base_level = int((main_road_weight * 6 + secondary_road_weight * 3 + local_roads) / total_weight * 20)

        hourly_pattern = []

        for hour in range(24):
            if 7 <= hour <= 9:
                factor = 1.8 if hour == 8 else 1.4
            elif 16 <= hour <= 19:
                factor = 2.0 if hour == 17 else 1.5
            elif 10 <= hour <= 15:
                factor = 1.2
            elif 20 <= hour <= 22:
                factor = 0.8
            else:
                factor = 0.4

            direction_bias = 1.1 if (hour in [8, 17]) else 1.0

            hourly_congestion = min(95, int(base_level * factor * direction_bias))
            hourly_pattern.append(hourly_congestion)

        return hourly_pattern

    def _find_longest_road(self, roads: list) -> dict:
        if not roads:
            return {"name": "No data", "length": 0}

        named_roads = [road for road in roads if road.get("name") != "Unnamed road"]
        if not named_roads:
            longest = max(roads, key=lambda x: x.get("length", 0))
            return {"name": "Unnamed road", "length": longest.get("length", 0)}

        longest_named = max(named_roads, key=lambda x: x.get("length", 0))
        return {
            "name": longest_named.get("name", "Unknown road"),
            "length": longest_named.get("length", 0)
        }