import random
import logging
import math
import hashlib
from typing import Dict, List, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoadNetworkGenerator:
    def __init__(self):
        self.default_bounds = [[50.45, 30.52], [50.44, 30.53]]
        self.min_improvement = 5
        self.max_improvement = 30
        self.building_buffer = 0.001
        self.road_buffer = 0.0005
        self.green_to_building_distance = 0.0008
        self.green_to_road_distance = 0.0006

    def generate_improved_network(self, current_analysis: Dict) -> Dict:
        logger.info("Початок генерації покращеного плану з collision detection")

        try:
            safe_analysis = self._make_data_safe(current_analysis)
            territory_hash = self._create_territory_hash(safe_analysis)
            random.seed(territory_hash)

            territory_analysis = self._analyze_territory_specifics(safe_analysis)
            collision_map = self._create_collision_map(safe_analysis)

            improvements = self._calculate_adaptive_improvements(safe_analysis, territory_analysis)

            improved_plan = self._create_smart_layout_plan(safe_analysis, improvements, territory_analysis,
                                                           collision_map)

            logger.info("Адаптивний план з розумним розміщенням створено")
            return improved_plan

        except Exception as e:
            logger.error(f"Критична помилка: {e}")
            return self._get_emergency_plan()

    def _create_collision_map(self, data: Dict) -> Dict:
        collision_map = {
            'buildings': [],
            'existing_roads': [],
            'existing_green': [],
            'road_intersections': [],
            'prohibited_zones': []
        }

        buildings_data = data.get('buildings_data', [])
        for building in buildings_data:
            if 'coordinates' in building and len(building['coordinates']) > 2:
                coords = building['coordinates']
                center = self._calculate_polygon_center(coords)
                bounds = self._calculate_polygon_bounds(coords)
                collision_map['buildings'].append({
                    'center': center,
                    'bounds': bounds,
                    'coordinates': coords,
                    'buffer_zone': self._expand_bounds(bounds, self.building_buffer)
                })

        roads_data = data.get('roads_data', [])
        for road in roads_data:
            if 'coordinates' in road and len(road['coordinates']) > 1:
                coords = road['coordinates']
                collision_map['existing_roads'].append({
                    'coordinates': coords,
                    'path_zones': self._create_road_buffer_zones(coords)
                })

        return collision_map

    def _calculate_polygon_center(self, coords: List[List[float]]) -> Tuple[float, float]:
        if not coords:
            return (0, 0)

        lats = [coord[0] for coord in coords if len(coord) >= 2]
        lngs = [coord[1] for coord in coords if len(coord) >= 2]

        if not lats or not lngs:
            return (0, 0)

        return (sum(lats) / len(lats), sum(lngs) / len(lngs))

    def _calculate_polygon_bounds(self, coords: List[List[float]]) -> Dict:
        if not coords:
            return {'min_lat': 0, 'max_lat': 0, 'min_lng': 0, 'max_lng': 0}

        lats = [coord[0] for coord in coords if len(coord) >= 2]
        lngs = [coord[1] for coord in coords if len(coord) >= 2]

        if not lats or not lngs:
            return {'min_lat': 0, 'max_lat': 0, 'min_lng': 0, 'max_lng': 0}

        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs)
        }

    def _expand_bounds(self, bounds: Dict, buffer: float) -> Dict:
        return {
            'min_lat': bounds['min_lat'] - buffer,
            'max_lat': bounds['max_lat'] + buffer,
            'min_lng': bounds['min_lng'] - buffer,
            'max_lng': bounds['max_lng'] + buffer
        }

    def _create_road_buffer_zones(self, coords: List[List[float]]) -> List[Dict]:
        buffer_zones = []

        for i in range(len(coords) - 1):
            start_lat, start_lng = coords[i][:2]
            end_lat, end_lng = coords[i + 1][:2]

            buffer_zone = {
                'min_lat': min(start_lat, end_lat) - self.road_buffer,
                'max_lat': max(start_lat, end_lat) + self.road_buffer,
                'min_lng': min(start_lng, end_lng) - self.road_buffer,
                'max_lng': max(start_lng, end_lng) + self.road_buffer
            }
            buffer_zones.append(buffer_zone)

        return buffer_zones

    def _is_green_location_safe(self, coords: List[List[float]], collision_map: Dict) -> bool:
        for coord in coords:
            lat, lng = coord[:2]

            for building in collision_map['buildings']:
                if self._point_in_bounds(lat, lng, building['buffer_zone']):
                    return False

            for road in collision_map['existing_roads']:
                for buffer_zone in road['path_zones']:
                    if self._point_in_bounds(lat, lng, buffer_zone):
                        return False

        return True

    def _is_road_location_safe(self, coords: List[List[float]], collision_map: Dict) -> bool:
        for coord in coords:
            lat, lng = coord[:2]

            for building in collision_map['buildings']:
                if self._point_in_bounds(lat, lng, building['buffer_zone']):
                    return False

        return True

    def _point_in_bounds(self, lat: float, lng: float, bounds: Dict) -> bool:
        return (bounds['min_lat'] <= lat <= bounds['max_lat'] and
                bounds['min_lng'] <= lng <= bounds['max_lng'])

    def _find_safe_green_location(self, bounds: List[List[float]], collision_map: Dict, size: float,
                                  attempts: int = 100) -> Tuple[float, float]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(attempts):
            margin = 0.002
            center_lat = se_lat + margin + random.random() * (nw_lat - se_lat - 2 * margin)
            center_lng = nw_lng + margin + random.random() * (se_lng - nw_lng - 2 * margin)

            test_coords = self._generate_tiny_organic_shape(center_lat, center_lng, size)

            if self._is_green_location_safe(test_coords, collision_map):
                return (center_lat, center_lng)

        return ((nw_lat + se_lat) / 2, (nw_lng + se_lng) / 2)

    def _create_smart_layout_plan(self, data: Dict, improvements: Dict, territory_analysis: Dict,
                                  collision_map: Dict) -> Dict:
        focus = improvements.get('focus', 'balanced')
        territory_type = territory_analysis['type']

        new_congestion, new_ecology, new_pedestrian, new_transport = self._calculate_improved_metrics(data,
                                                                                                      improvements,
                                                                                                      focus)

        green_spaces = self._create_safe_green_spaces(data, territory_analysis, improvements, collision_map)
        roads = self._create_safe_roads(data, territory_analysis, improvements, collision_map)
        transport_stops = self._create_smart_transport_stops(data, territory_analysis, improvements, collision_map,
                                                             roads)

        roundabouts = self._create_safe_roundabouts(data, territory_analysis, collision_map)

        plan = {
            'congestion': round(new_congestion, 1),
            'ecology': round(new_ecology, 1),
            'pedestrian_friendly': round(new_pedestrian, 1),
            'public_transport': round(new_transport, 1),
            'road_count': data['road_count'] + len(roads) + len(roundabouts),
            'bounds': data['bounds'],
            'green_spaces': green_spaces,
            'roads': roads + roundabouts,
            'transport_stops': transport_stops,
            'improvements_summary': {
                'total_new_objects': len(green_spaces) + len(roads) + len(transport_stops) + len(roundabouts),
                'priority_areas': [focus, territory_type],
                'territory_type': territory_type,
                'main_problems': territory_analysis['problems'],
                'estimated_cost': self._estimate_cost(territory_analysis, improvements),
                'implementation_time': self._estimate_time(territory_analysis, improvements),
                'collision_avoidance': True
            }
        }

        return plan

    def _create_safe_green_spaces(self, data: Dict, territory_analysis: Dict, improvements: Dict,
                                  collision_map: Dict) -> List[Dict]:
        count = improvements.get('green_spaces_count', 2)
        bounds = data['bounds']
        territory_type = territory_analysis['type']

        if territory_type == 'industrial':
            space_types = ['park', 'forest', 'buffer_zone']
        elif territory_type == 'urban_dense':
            space_types = ['square', 'pocket_park']
        else:
            space_types = ['park', 'garden', 'square']

        spaces = []
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]
        lat_range = abs(nw_lat - se_lat)
        lng_range = abs(se_lng - nw_lng)

        names = ['Центральний', 'Мирний', 'Сонячний', 'Зелений', 'Дружби', 'Тихий']

        for i in range(min(count, 6)):
            space_type = space_types[i % len(space_types)]

            base_size = min(lat_range, lng_range) * 0.03
            size_variation = random.uniform(0.5, 1.2)
            final_size = base_size * size_variation

            center_lat, center_lng = self._find_safe_green_location(bounds, collision_map, final_size)

            shape_type = random.choice(['organic', 'square', 'triangle', 'circle', 'random'])
            coords = self._generate_small_shape(center_lat, center_lng, final_size, shape_type)

            if not self._is_green_location_safe(coords, collision_map):
                continue

            area = self._calculate_polygon_area(coords)

            spaces.append({
                'id': f'safe_green_{i}',
                'name': f'{space_type.replace("_", " ").capitalize()} {names[i % len(names)]}',
                'type': space_type,
                'area': round(area, 2),
                'coordinates': coords,
                'collision_safe': True
            })

        return spaces

    def _generate_small_shape(self, center_lat: float, center_lng: float, size: float, shape_type: str) -> List[
        List[float]]:
        if shape_type == 'square':
            return self._generate_tiny_square_shape(center_lat, center_lng, size)
        elif shape_type == 'triangle':
            return self._generate_tiny_triangle_shape(center_lat, center_lng, size)
        elif shape_type == 'circle':
            return self._generate_tiny_circle_shape(center_lat, center_lng, size)
        elif shape_type == 'random':
            return self._generate_tiny_random_shape(center_lat, center_lng, size)
        else:
            return self._generate_tiny_organic_shape(center_lat, center_lng, size)

    def _generate_tiny_square_shape(self, center_lat: float, center_lng: float, size: float) -> List[List[float]]:
        half_size = size * 0.3
        coords = [
            [center_lat + half_size, center_lng - half_size],
            [center_lat + half_size, center_lng + half_size],
            [center_lat - half_size, center_lng + half_size],
            [center_lat - half_size, center_lng - half_size],
            [center_lat + half_size, center_lng - half_size]
        ]
        return coords

    def _generate_tiny_triangle_shape(self, center_lat: float, center_lng: float, size: float) -> List[List[float]]:
        height = size * 0.4
        half_base = size * 0.3
        coords = [
            [center_lat + height, center_lng],
            [center_lat - height / 2, center_lng - half_base],
            [center_lat - height / 2, center_lng + half_base],
            [center_lat + height, center_lng]
        ]
        return coords

    def _generate_tiny_circle_shape(self, center_lat: float, center_lng: float, size: float) -> List[List[float]]:
        radius = size * 0.2
        num_points = 8
        coords = []
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            lat = center_lat + radius * math.cos(angle)
            lng = center_lng + radius * math.sin(angle)
            coords.append([lat, lng])
        return coords

    def _generate_tiny_random_shape(self, center_lat: float, center_lng: float, size: float) -> List[List[float]]:
        num_points = random.randint(4, 7)
        coords = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            variation = random.uniform(0.7, 1.3)
            radius = size * 0.2 * variation
            lat = center_lat + radius * math.cos(angle + random.uniform(-0.2, 0.2))
            lng = center_lng + radius * math.sin(angle + random.uniform(-0.2, 0.2))
            coords.append([lat, lng])
        coords.append(coords[0])
        return coords

    def _generate_tiny_organic_shape(self, center_lat: float, center_lng: float, size: float) -> List[List[float]]:
        num_points = random.randint(5, 8)
        coords = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            radius_variation = random.uniform(0.8, 1.2)
            radius = size * 0.15 * radius_variation
            angle_noise = random.uniform(-0.3, 0.3)
            lat = center_lat + radius * math.cos(angle + angle_noise)
            lng = center_lng + radius * math.sin(angle + angle_noise)
            coords.append([lat, lng])
        coords.append(coords[0])
        return coords

    def _create_safe_roads(self, data: Dict, territory_analysis: Dict, improvements: Dict, collision_map: Dict) -> List[
        Dict]:
        count = improvements.get('new_roads', 2)
        bounds = data['bounds']
        territory_type = territory_analysis['type']

        if territory_type == 'urban_dense':
            road_types = ['tertiary', 'residential']
            lane_counts = [2, 2]
        elif territory_type == 'traffic_heavy':
            road_types = ['primary', 'secondary']
            lane_counts = [4, 4]
        else:
            road_types = ['secondary', 'tertiary', 'residential']
            lane_counts = [4, 2, 2]

        roads = []
        road_names = ['Нова', 'Центральна', 'Головна', 'Паркова', 'Об\'їзна', 'З\'єднувальна']

        for i in range(min(count, 6)):
            road_type = road_types[i % len(road_types)]
            lanes = lane_counts[i % len(lane_counts)]

            coords = self._create_safe_road_path(bounds, collision_map, i, count)

            if not self._is_road_location_safe(coords, collision_map):
                continue

            length = self._calculate_path_length(coords)

            roads.append({
                'id': f'safe_road_{i}',
                'name': f'{road_names[i % len(road_names)]} вулиця',
                'type': road_type,
                'lanes': lanes,
                'length': length,
                'coordinates': coords,
                'collision_safe': True
            })

        return roads

    def _create_safe_road_path(self, bounds: List[List[float]], collision_map: Dict, road_index: int,
                               total_roads: int) -> List[List[float]]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        path_type = random.choice(['straight', 'curved', 'l_shape', 'u_shape'])

        if path_type == 'straight':
            return self._create_straight_safe_path(bounds, collision_map, road_index, total_roads)
        elif path_type == 'curved':
            return self._create_curved_safe_path(bounds, collision_map, road_index, total_roads)
        elif path_type == 'l_shape':
            return self._create_l_shape_safe_path(bounds, collision_map)
        else:
            return self._create_u_shape_safe_path(bounds, collision_map)

    def _create_straight_safe_path(self, bounds: List[List[float]], collision_map: Dict, road_index: int,
                                   total_roads: int) -> List[List[float]]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(20):
            if road_index % 2 == 0:
                road_lat = se_lat + (nw_lat - se_lat) * (0.2 + 0.6 * random.random())
                start_lng = nw_lng + 0.001
                end_lng = se_lng - 0.001
                coords = [[road_lat, start_lng], [road_lat, end_lng]]
            else:
                road_lng = nw_lng + (se_lng - nw_lng) * (0.2 + 0.6 * random.random())
                start_lat = nw_lat - 0.001
                end_lat = se_lat + 0.001
                coords = [[start_lat, road_lng], [end_lat, road_lng]]

            if self._is_road_location_safe(coords, collision_map):
                return coords

        return [[nw_lat - 0.001, nw_lng + 0.001], [se_lat + 0.001, se_lng - 0.001]]

    def _create_curved_safe_path(self, bounds: List[List[float]], collision_map: Dict, road_index: int,
                                 total_roads: int) -> List[List[float]]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(20):
            start_lat = se_lat + 0.001 + random.random() * (nw_lat - se_lat - 0.002)
            start_lng = nw_lng + 0.001 + random.random() * (se_lng - nw_lng - 0.002)

            end_lat = se_lat + 0.001 + random.random() * (nw_lat - se_lat - 0.002)
            end_lng = nw_lng + 0.001 + random.random() * (se_lng - nw_lng - 0.002)

            num_points = random.randint(3, 5)
            coords = [[start_lat, start_lng]]

            for i in range(1, num_points - 1):
                progress = i / (num_points - 1)
                lat = start_lat + (end_lat - start_lat) * progress + random.uniform(-0.0003, 0.0003)
                lng = start_lng + (end_lng - start_lng) * progress + random.uniform(-0.0003, 0.0003)
                coords.append([lat, lng])

            coords.append([end_lat, end_lng])

            if self._is_road_location_safe(coords, collision_map):
                return coords

        return self._create_straight_safe_path(bounds, collision_map, road_index, total_roads)

    def _create_l_shape_safe_path(self, bounds: List[List[float]], collision_map: Dict) -> List[List[float]]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(20):
            start_lat = se_lat + 0.001 + random.random() * (nw_lat - se_lat - 0.002)
            start_lng = nw_lng + 0.001 + random.random() * (se_lng - nw_lng - 0.002)

            mid_lat = start_lat + random.uniform(-0.001, 0.001)
            mid_lng = start_lng + random.uniform(0.0005, 0.002)

            end_lat = mid_lat + random.uniform(0.0005, 0.002)
            end_lng = mid_lng

            coords = [[start_lat, start_lng], [mid_lat, mid_lng], [end_lat, end_lng]]

            if self._is_road_location_safe(coords, collision_map):
                return coords

        return self._create_straight_safe_path(bounds, collision_map, 0, 1)

    def _create_u_shape_safe_path(self, bounds: List[List[float]], collision_map: Dict) -> List[List[float]]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(20):
            start_lat = se_lat + 0.001 + random.random() * (nw_lat - se_lat - 0.002)
            start_lng = nw_lng + 0.001 + random.random() * (se_lng - nw_lng - 0.002)

            mid1_lat = start_lat + random.uniform(0.0005, 0.0015)
            mid1_lng = start_lng + random.uniform(0.0005, 0.0015)

            mid2_lat = mid1_lat
            mid2_lng = mid1_lng + random.uniform(0.0005, 0.0015)

            end_lat = start_lat
            end_lng = mid2_lng

            coords = [[start_lat, start_lng], [mid1_lat, mid1_lng], [mid2_lat, mid2_lng], [end_lat, end_lng]]

            if self._is_road_location_safe(coords, collision_map):
                return coords

        return self._create_straight_safe_path(bounds, collision_map, 0, 1)

    def _create_safe_roundabouts(self, data: Dict, territory_analysis: Dict, collision_map: Dict) -> List[Dict]:
        bounds = data['bounds']
        territory_type = territory_analysis['type']
        existing_roads = data.get('roads_data', [])

        if len(existing_roads) < 2:
            return []

        roundabouts = []
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]
        lat_range = nw_lat - se_lat
        lng_range = se_lng - nw_lng

        max_roundabouts = 1 if territory_type == 'urban_dense' else 2

        for i in range(max_roundabouts):
            for attempt in range(50):
                center_lat = se_lat + 0.001 + random.random() * (lat_range - 0.002)
                center_lng = nw_lng + 0.001 + random.random() * (lng_range - 0.002)

                if territory_type == 'traffic_heavy':
                    radius = random.uniform(0.0003, 0.0006)
                elif territory_type == 'urban_dense':
                    radius = random.uniform(0.0002, 0.0004)
                else:
                    radius = random.uniform(0.0002, 0.0005)

                circle_coords = self._generate_circle_coordinates(center_lat, center_lng, radius, 12)

                if not self._is_road_location_safe(circle_coords, collision_map):
                    continue

                roundabouts.append({
                    'id': f'safe_roundabout_{i}',
                    'name': f'Дорожнє коло №{i + 1}',
                    'type': 'roundabout',
                    'lanes': 2,
                    'radius': radius * 111000,
                    'coordinates': circle_coords,
                    'collision_safe': True
                })
                break

        return roundabouts

    def _generate_circle_coordinates(self, center_lat: float, center_lng: float, radius: float, num_points: int) -> \
    List[List[float]]:
        coords = []
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            lat = center_lat + radius * math.cos(angle)
            lng = center_lng + radius * math.sin(angle)
            coords.append([lat, lng])
        return coords

    def _create_smart_transport_stops(self, data: Dict, territory_analysis: Dict, improvements: Dict,
                                      collision_map: Dict, roads: List[Dict]) -> List[Dict]:
        count = improvements.get('transport_stops', 2)
        bounds = data['bounds']

        stops = []

        for i in range(count):
            for attempt in range(30):
                stop_lat, stop_lng = self._find_safe_road_location(bounds, collision_map)

                if self._is_road_location_safe([[stop_lat, stop_lng]], collision_map):
                    stops.append({
                        'id': f'safe_stop_{i}',
                        'name': f'Зупинка №{i + 1}',
                        'type': 'bus_stop',
                        'coordinates': [stop_lat, stop_lng],
                        'collision_safe': True
                    })
                    break

        return stops

    def _find_safe_road_location(self, bounds: List[List[float]], collision_map: Dict) -> Tuple[float, float]:
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        for attempt in range(50):
            lat = se_lat + 0.001 + random.random() * (nw_lat - se_lat - 0.002)
            lng = nw_lng + 0.001 + random.random() * (se_lng - nw_lng - 0.002)

            if self._is_road_location_safe([[lat, lng]], collision_map):
                return (lat, lng)

        return ((nw_lat + se_lat) / 2, (nw_lng + se_lng) / 2)

    def _calculate_improved_metrics(self, data: Dict, improvements: Dict, focus: str) -> Tuple[
        float, float, float, float]:
        current_congestion = data.get('congestion', 50)
        current_ecology = data.get('ecology', 50)
        current_pedestrian = data.get('pedestrian_friendly', 50)
        current_transport = data.get('public_transport', 50)

        congestion_improvement = improvements.get('congestion_reduction', random.randint(15, 25))
        ecology_improvement = random.randint(15, 25)
        pedestrian_improvement = random.randint(10, 20)
        transport_improvement = random.randint(15, 25)

        if focus == 'traffic_flow':
            congestion_improvement += 10
            transport_improvement += 5
        elif focus == 'sustainability':
            ecology_improvement += 15
            pedestrian_improvement += 5
        elif focus == 'efficiency':
            congestion_improvement += 5
            transport_improvement += 10

        total_objects = (improvements.get('new_roads', 0) +
                         improvements.get('green_spaces_count', 0) +
                         improvements.get('transport_stops', 0))
        object_bonus = min(10, total_objects * 2)

        new_congestion = max(5, current_congestion - congestion_improvement)
        new_ecology = min(95, current_ecology + ecology_improvement + object_bonus)
        new_pedestrian = min(95, current_pedestrian + pedestrian_improvement + object_bonus // 2)
        new_transport = min(95, current_transport + transport_improvement + object_bonus // 2)

        return new_congestion, new_ecology, new_pedestrian, new_transport

    def _create_territory_hash(self, data: Dict) -> int:
        bounds = data['bounds']
        key_metrics = [
            data['congestion'], data['ecology'],
            data['pedestrian_friendly'], data['public_transport'],
            bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]
        ]

        hash_string = "_".join([f"{x:.3f}" for x in key_metrics])
        hash_object = hashlib.md5(hash_string.encode())
        return int(hash_object.hexdigest()[:8], 16)

    def _analyze_territory_specifics(self, data: Dict) -> Dict:
        bounds = data['bounds']
        nw_lat, nw_lng = bounds[0]
        se_lat, se_lng = bounds[1]

        lat_range = abs(nw_lat - se_lat)
        lng_range = abs(se_lng - nw_lng)
        area_size = lat_range * lng_range

        territory_type = self._determine_territory_type(data, area_size)
        problem_areas = self._identify_problem_areas(data)
        priorities = self._calculate_priorities(data)

        return {
            'type': territory_type,
            'size': area_size,
            'lat_range': lat_range,
            'lng_range': lng_range,
            'problems': problem_areas,
            'priorities': priorities
        }

    def _determine_territory_type(self, data: Dict, area_size: float) -> str:
        road_count = data.get('road_count', 0)
        congestion = data['congestion']
        ecology = data['ecology']

        if area_size < 0.001:
            return 'micro_district'
        elif road_count > 20 and congestion > 60:
            return 'urban_dense'
        elif ecology > 70 and road_count < 10:
            return 'green_residential'
        elif congestion > 70:
            return 'traffic_heavy'
        elif ecology < 30:
            return 'industrial'
        else:
            return 'mixed_residential'

    def _identify_problem_areas(self, data: Dict) -> List[str]:
        problems = []
        if data['congestion'] > 70:
            problems.append('high_traffic')
        if data['ecology'] < 40:
            problems.append('low_green')
        if data['pedestrian_friendly'] < 40:
            problems.append('poor_walkability')
        if data['public_transport'] < 40:
            problems.append('inadequate_transit')
        return problems

    def _calculate_priorities(self, data: Dict) -> Dict[str, int]:
        priorities = {}
        priorities['traffic'] = max(0, data['congestion'] - 30)
        priorities['ecology'] = max(0, 80 - data['ecology'])
        priorities['walkability'] = max(0, 80 - data['pedestrian_friendly'])
        priorities['transit'] = max(0, 80 - data['public_transport'])
        return priorities

    def _calculate_adaptive_improvements(self, data: Dict, territory_analysis: Dict) -> Dict:
        improvements = {}
        territory_type = territory_analysis['type']
        problems = territory_analysis['problems']
        priorities = territory_analysis['priorities']

        if territory_type == 'urban_dense':
            improvements.update(self._urban_dense_strategy(data, priorities))
        elif territory_type == 'green_residential':
            improvements.update(self._green_residential_strategy(data, priorities))
        elif territory_type == 'traffic_heavy':
            improvements.update(self._traffic_heavy_strategy(data, priorities))
        elif territory_type == 'industrial':
            improvements.update(self._industrial_strategy(data, priorities))
        else:
            improvements.update(self._mixed_residential_strategy(data, priorities))

        if 'high_traffic' in problems:
            improvements['bypass_roads'] = True
        if 'low_green' in problems:
            improvements['green_corridors'] = True

        return improvements

    def _urban_dense_strategy(self, data: Dict, priorities: Dict) -> Dict:
        return {
            'congestion_reduction': random.randint(15, 25),
            'new_roads': random.randint(1, 2),
            'green_spaces_count': random.randint(2, 4),
            'transport_stops': random.randint(3, 5),
            'focus': 'public_transport'
        }

    def _green_residential_strategy(self, data: Dict, priorities: Dict) -> Dict:
        return {
            'congestion_reduction': random.randint(5, 15),
            'new_roads': random.randint(1, 3),
            'green_spaces_count': random.randint(1, 3),
            'transport_stops': random.randint(2, 4),
            'focus': 'connectivity'
        }

    def _traffic_heavy_strategy(self, data: Dict, priorities: Dict) -> Dict:
        return {
            'congestion_reduction': random.randint(25, 35),
            'new_roads': random.randint(3, 5),
            'green_spaces_count': random.randint(2, 3),
            'transport_stops': random.randint(4, 6),
            'focus': 'traffic_flow'
        }

    def _industrial_strategy(self, data: Dict, priorities: Dict) -> Dict:
        return {
            'congestion_reduction': random.randint(10, 20),
            'new_roads': random.randint(2, 4),
            'green_spaces_count': random.randint(4, 6),
            'transport_stops': random.randint(3, 5),
            'focus': 'ecology'
        }

    def _mixed_residential_strategy(self, data: Dict, priorities: Dict) -> Dict:
        return {
            'congestion_reduction': random.randint(10, 20),
            'new_roads': random.randint(2, 3),
            'green_spaces_count': random.randint(2, 4),
            'transport_stops': random.randint(2, 4),
            'focus': 'balanced'
        }

    def _make_data_safe(self, data: Any) -> Dict:
        if not isinstance(data, dict):
            data = {}

        safe_data = {
            'congestion': self._safe_number(data.get('congestion'), 50, 0, 100),
            'ecology': self._safe_number(data.get('ecology'), 50, 0, 100),
            'pedestrian_friendly': self._safe_number(data.get('pedestrian_friendly'), 50, 0, 100),
            'public_transport': self._safe_number(data.get('public_transport'), 50, 0, 100),
            'road_count': self._safe_number(data.get('road_count'), 10, 0, 1000),
            'area': self._safe_number(data.get('area'), 2.0, 0.1, 100.0),
            'bounds': self._safe_bounds(data.get('bounds')),
            'buildings_data': data.get('buildings_data', []),
            'green_spaces_data': data.get('green_spaces_data', []),
            'roads_data': data.get('roads_data', [])
        }

        return safe_data

    def _safe_number(self, value: Any, default: float, min_val: float, max_val: float) -> float:
        try:
            if value is None:
                return default
            num = float(value)
            return max(min_val, min(max_val, num))
        except (ValueError, TypeError):
            return default

    def _safe_bounds(self, bounds: Any) -> List[List[float]]:
        try:
            if not bounds or len(bounds) != 2:
                return self.default_bounds.copy()

            nw = bounds[0]
            se = bounds[1]

            if len(nw) != 2 or len(se) != 2:
                return self.default_bounds.copy()

            nw_lat = float(nw[0])
            nw_lng = float(nw[1])
            se_lat = float(se[0])
            se_lng = float(se[1])

            if nw_lat < se_lat:
                nw_lat, se_lat = se_lat, nw_lat
            if nw_lng > se_lng:
                nw_lng, se_lng = se_lng, nw_lng

            return [[nw_lat, nw_lng], [se_lat, se_lng]]

        except (ValueError, TypeError, IndexError):
            return self.default_bounds.copy()

    def _calculate_polygon_area(self, coords: List[List[float]]) -> float:
        if len(coords) < 3:
            return 0

        area = 0
        for i in range(len(coords) - 1):
            area += coords[i][0] * coords[i + 1][1]
            area -= coords[i + 1][0] * coords[i][1]

        area = abs(area) / 2
        area_hectares = area * 111000 * 111000 / 10000

        return max(0.01, area_hectares)

    def _calculate_path_length(self, coords: List[List[float]]) -> float:
        if len(coords) < 2:
            return 0

        total_length = 0
        for i in range(len(coords) - 1):
            lat_diff = coords[i + 1][0] - coords[i][0]
            lng_diff = coords[i + 1][1] - coords[i][1]
            segment_length = math.sqrt(lat_diff ** 2 + lng_diff ** 2) * 111
            total_length += segment_length

        return round(total_length, 1)

    def _estimate_cost(self, territory_analysis: Dict, improvements: Dict) -> str:
        territory_type = territory_analysis['type']
        total_objects = improvements.get('green_spaces_count', 0) + improvements.get('new_roads', 0)

        if territory_type == 'urban_dense' or total_objects > 8:
            return 'high'
        elif territory_type == 'industrial' or total_objects > 5:
            return 'medium'
        else:
            return 'low'

    def _estimate_time(self, territory_analysis: Dict, improvements: Dict) -> str:
        territory_type = territory_analysis['type']
        focus = improvements.get('focus', 'balanced')

        if territory_type == 'urban_dense' and focus == 'traffic_flow':
            return '12-18 months'
        elif focus == 'ecology' or territory_type == 'green_residential':
            return '6-9 months'
        else:
            return '9-12 months'

    def _get_emergency_plan(self) -> Dict:
        return {
            'congestion': 35.0,
            'ecology': 65.0,
            'pedestrian_friendly': 60.0,
            'public_transport': 55.0,
            'road_count': 12,
            'bounds': self.default_bounds,
            'green_spaces': [],
            'roads': [],
            'transport_stops': [],
            'improvements_summary': {
                'total_new_objects': 0,
                'priority_areas': ['emergency'],
                'territory_type': 'mixed_residential',
                'main_problems': ['general'],
                'estimated_cost': 'low',
                'implementation_time': '3-6 months',
                'collision_avoidance': True
            }
        }