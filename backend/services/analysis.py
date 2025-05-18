from math import radians, cos, sin, asin, sqrt
from services.osm_data import OSMDataFetcher, haversine

class AreaAnalyzer:
    def __init__(self):
        self.osm_fetcher = OSMDataFetcher()

    def perform_analysis(self, nw_lat, nw_lng, se_lat, se_lng):
        north = max(nw_lat, se_lat)
        south = min(nw_lat, se_lat)
        east = max(nw_lng, se_lng)
        west = min(nw_lng, se_lng)

        osm_data = self.osm_fetcher.get_area_data(north, west, south, east)
        area = self._calculate_area(north, west, south, east)
        roads, road_count, road_types = self._extract_road_data(osm_data)
        green_spaces, water_features = self._extract_green_water_data(osm_data)

        # Calculate pedestrian and public transport scores
        pedestrian_friendly = self._calculate_pedestrian_score(roads, road_types)
        public_transport = self._calculate_transport_score(osm_data)

        return {
            "bounds": [[north, west], [south, east]],
            "area": round(area, 2),
            "road_count": road_count,
            "road_types": road_types,
            "longest_road": self._find_longest_road(roads),
            "congestion": self._calculate_congestion(road_types),
            "ecology": self._calculate_ecology_score(green_spaces, water_features, area),
            "pedestrian_friendly": pedestrian_friendly,
            "public_transport": public_transport,
            "hourly_congestion": self._estimate_hourly_congestion(road_types)
        }

    def _calculate_area(self, north, west, south, east):
        """Calculate the area of the bounding box in square kilometers"""
        try:
            avg_lat = (north + south) / 2
            width = haversine(west, avg_lat, east, avg_lat)
            height = haversine(west, north, west, south)
            return round(width * height, 2)
        except Exception as e:
            logger.error(f"Error calculating area: {e}")
            return 1.0

    def _extract_road_data(self, osm_data):
        """Extract road data from OSM response"""
        roads = []
        road_count = 0
        road_types = {
            "Головні": 0, "Другорядні": 0, "Місцеві": 0,
            "Пішохідні": 0, "Велосипедні": 0
        }

        nodes = {e["id"]: (e["lat"], e["lon"])
                 for e in osm_data.get("elements", []) if e["type"] == "node"}

        for element in osm_data.get("elements", []):
            if element["type"] == "way" and "highway" in element.get("tags", {}):
                road_count += 1
                highway_type = element["tags"]["highway"]
                length = self._calculate_road_length(element, nodes)

                roads.append({
                    "id": element["id"],
                    "type": highway_type,
                    "name": element["tags"].get("name", "Unnamed road"),
                    "length": round(length, 2)
                })

                self._categorize_road(road_types, highway_type, element.get("tags", {}))

        return roads, road_count, road_types

    def _calculate_road_length(self, element, nodes):
        """Calculate the length of a road segment"""
        length = 0
        if "nodes" in element and len(element["nodes"]) > 1:
            for i in range(len(element["nodes"]) - 1):
                node1, node2 = element["nodes"][i], element["nodes"][i + 1]
                if node1 in nodes and node2 in nodes:
                    lat1, lon1 = nodes[node1]
                    lat2, lon2 = nodes[node2]
                    length += haversine(lon1, lat1, lon2, lat2)
        return length

    def _categorize_road(self, road_types, highway_type, tags):
        """Categorize roads by type"""
        if highway_type in ["motorway", "trunk", "primary"]:
            road_types["Головні"] += 1
        elif highway_type in ["secondary", "tertiary"]:
            road_types["Другорядні"] += 1
        elif highway_type in ["residential", "service", "unclassified"]:
            road_types["Місцеві"] += 1
        elif highway_type in ["pedestrian", "footway", "path", "steps"]:
            road_types["Пішохідні"] += 1
        elif highway_type == "cycleway" or tags.get("bicycle") == "designated":
            road_types["Велосипедні"] += 1

    def _extract_green_water_data(self, osm_data):
        """Extract data about green spaces and water features"""
        green_spaces, water_features = [], []

        for element in osm_data.get("elements", []):
            if element["type"] in ["way", "relation"] and "tags" in element:
                tags = element["tags"]
                if tags.get("leisure") == "park" or tags.get("natural") == "wood" or tags.get("landuse") in ["forest",
                                                                                                             "meadow",
                                                                                                             "grass"]:
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

    def _calculate_score(self, value, max_value, weight=1):
        """Calculate a normalized score between 10 and 95"""
        return min(95, max(10, int(value * weight / max(max_value, 0.1))))

    def _calculate_ecology_score(self, green_spaces, water_features, area):
        """Calculate ecology score based on green spaces and water features"""
        green_score = self._calculate_score(len(green_spaces), area, 10)
        water_score = self._calculate_score(len(water_features), area, 15)
        return int(0.7 * green_score + 0.3 * water_score)

    def _calculate_pedestrian_score(self, roads, road_types):
        """Calculate pedestrian-friendliness score"""
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 50
        return self._calculate_score(road_types["Пішохідні"], total_roads, 300)

    def _calculate_transport_score(self, osm_data):
        """Calculate public transport accessibility score"""
        transport_stops = sum(
            1 for e in osm_data.get("elements", [])
            if e["type"] == "node" and "tags" in e and (
                    e["tags"].get("public_transport") in ["stop_position", "platform"] or
                    e["tags"].get("highway") == "bus_stop" or
                    e["tags"].get("railway") in ["station", "halt", "tram_stop"]
            )
        )
        return self._calculate_score(transport_stops, 1, 5)

    def _calculate_congestion(self, road_types):
        """Calculate congestion score based on road types"""
        total_roads = sum(road_types.values())
        if total_roads == 0:
            return 50
        return self._calculate_score(road_types["Головні"], total_roads, 150)

    def _estimate_hourly_congestion(self, road_types):
        """Estimate hourly congestion patterns"""
        base_level = min(40, int((road_types["Головні"] * 5 + road_types["Другорядні"] * 3) /
                                 max(sum(road_types.values()), 1) * 100))

        hourly_pattern = []
        for hour in range(24):
            if 7 <= hour <= 9:
                factor = 2.0 + (hour - 7) * 0.5
            elif 16 <= hour <= 19:
                factor = 2.0 + (1 - abs(hour - 17.5) / 1.5)
            elif 10 <= hour <= 15:
                factor = 1.3
            elif 20 <= hour <= 23:
                factor = 1.0 - (hour - 20) * 0.15
            else:
                factor = 0.5

            hourly_pattern.append(min(95, int(base_level * factor)))
        return hourly_pattern

    def _find_longest_road(self, roads):
        """Find the longest named road in the area"""
        if not roads:
            return {"name": "No data", "length": 0}

        named_roads = [r for r in roads if r.get("name") != "Unnamed road"]
        if not named_roads:
            longest = max(roads, key=lambda x: x.get("length", 0))
            return {"name": "Unnamed road", "length": longest.get("length", 0)}

        longest_named = max(named_roads, key=lambda x: x.get("length", 0))
        return {"name": longest_named.get("name", "Unknown road"),
                "length": longest_named.get("length", 0)}
