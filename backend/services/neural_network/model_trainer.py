import numpy as np
import os
import json
import random
import hashlib
import math
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RoadNetworkTrainer:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.neural_model_file = os.path.join(self.models_dir, 'neural_weights.json')
        self.territory_patterns_file = os.path.join(self.models_dir, 'territory_patterns.json')

        self.input_features = 18
        self.hidden_layers = [32, 24, 16]
        self.output_features = 12

        self.weights = self._initialize_neural_network()

        self.territory_patterns = self._initialize_territory_patterns()

        self.safe_distances = {
            'building_to_road': 0.0005,
            'building_to_green': 0.0008,
            'road_to_green': 0.0003,
            'green_to_green': 0.001,
            'transport_to_building': 0.0006,
            'roundabout_min_distance': 0.002
        }

        self.context_factors = {
            'population_density': 0.0,
            'economic_level': 0.0,
            'geographic_constraints': 0.0,
            'existing_infrastructure': 0.0,
            'environmental_sensitivity': 0.0
        }

    def _initialize_neural_network(self):
        np.random.seed(42)
        weights = {}

        layer_sizes = [self.input_features] + self.hidden_layers + [self.output_features]

        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            std = np.sqrt(2.0 / fan_in)

            weights[f'W{i}'] = np.random.normal(0, std, (fan_in, fan_out))
            weights[f'b{i}'] = np.zeros(fan_out)

        return weights

    def _initialize_territory_patterns(self):
        return {
            'urban_dense': {
                'priority_weights': [0.9, 0.6, 0.8, 0.9, 0.7, 0.5, 0.8, 0.6, 0.7, 0.8, 0.6, 0.7],
                'constraints': {
                    'max_green_spaces': 4,
                    'prefer_vertical': True,
                    'min_transport': 6,
                    'roundabout_priority': 0.9,
                    'avoid_green_road_conflict': True
                },
                'optimization_focus': 'space_efficiency',
                'roundabout_logic': 'intersection_heavy'
            },
            'suburban': {
                'priority_weights': [0.6, 0.8, 0.7, 0.6, 0.8, 0.7, 0.6, 0.7, 0.8, 0.7, 0.6, 0.8],
                'constraints': {
                    'max_green_spaces': 6,
                    'prefer_horizontal': True,
                    'min_transport': 3,
                    'roundabout_priority': 0.6,
                    'green_distribution': 'distributed'
                },
                'optimization_focus': 'quality_of_life',
                'roundabout_logic': 'major_intersections'
            },
            'industrial': {
                'priority_weights': [0.8, 0.4, 0.5, 0.7, 0.9, 0.8, 0.7, 0.6, 0.5, 0.6, 0.8, 0.7],
                'constraints': {
                    'max_green_spaces': 8,
                    'buffer_zones': True,
                    'heavy_transport': True,
                    'roundabout_priority': 0.8,
                    'green_as_buffers': True
                },
                'optimization_focus': 'environmental_mitigation',
                'roundabout_logic': 'traffic_flow'
            },
            'rural': {
                'priority_weights': [0.4, 0.9, 0.8, 0.5, 0.6, 0.8, 0.4, 0.5, 0.9, 0.7, 0.5, 0.6],
                'constraints': {
                    'preserve_nature': True,
                    'minimal_intervention': True,
                    'roundabout_priority': 0.3,
                    'organic_roads': True
                },
                'optimization_focus': 'conservation',
                'roundabout_logic': 'minimal'
            },
            'mixed_residential': {
                'priority_weights': [0.7, 0.7, 0.8, 0.7, 0.6, 0.6, 0.7, 0.6, 0.7, 0.7, 0.6, 0.7],
                'constraints': {
                    'balanced_approach': True,
                    'flexible_zoning': True,
                    'roundabout_priority': 0.7,
                    'mixed_development': True
                },
                'optimization_focus': 'balanced_development',
                'roundabout_logic': 'balanced'
            },
            'green_residential': {
                'priority_weights': [0.5, 0.9, 0.9, 0.4, 0.6, 0.8, 0.6, 0.5, 0.9, 0.8, 0.4, 0.6],
                'constraints': {
                    'preserve_green': True,
                    'eco_friendly': True,
                    'low_density': True,
                    'roundabout_priority': 0.4,
                    'green_corridors': True
                },
                'optimization_focus': 'environmental_harmony',
                'roundabout_logic': 'eco_friendly'
            },
            'traffic_heavy': {
                'priority_weights': [0.9, 0.5, 0.6, 0.9, 0.8, 0.6, 0.8, 0.8, 0.5, 0.7, 0.9, 0.8],
                'constraints': {
                    'traffic_flow': True,
                    'bypass_roads': True,
                    'smart_signals': True,
                    'roundabout_priority': 0.95,
                    'traffic_optimization': True
                },
                'optimization_focus': 'traffic_optimization',
                'roundabout_logic': 'maximum_flow'
            }
        }

    def extract_comprehensive_features(self, analysis: Dict) -> np.ndarray:
        congestion = analysis.get('congestion', 50) / 100.0
        ecology = analysis.get('ecology', 50) / 100.0
        pedestrian = analysis.get('pedestrian_friendly', 50) / 100.0
        transport = analysis.get('public_transport', 50) / 100.0

        bounds = analysis.get('bounds', [[50.45, 30.52], [50.44, 30.53]])
        area = self._calculate_area(bounds)
        aspect_ratio = self._calculate_aspect_ratio(bounds)

        roads_data = analysis.get('roads_data', [])
        buildings_data = analysis.get('buildings_data', [])
        green_data = analysis.get('green_spaces_data', [])

        road_density = len(roads_data) / max(area, 0.01)
        building_density = len(buildings_data) / max(area, 0.01)
        green_density = len(green_data) / max(area, 0.01)

        road_quality = self._assess_road_network_quality(roads_data)
        connectivity = self._calculate_connectivity(roads_data, buildings_data)
        green_distribution = self._assess_green_distribution(green_data, bounds)

        population_density = self._estimate_population_density(buildings_data, area)
        economic_indicator = self._estimate_economic_level(analysis)

        congestion_severity = max(0, congestion - 0.6)
        ecological_deficit = max(0, 0.6 - ecology)

        intersection_density = self._calculate_intersection_potential(roads_data)
        green_fragmentation = self._calculate_green_fragmentation(green_data, bounds)
        transport_coverage = self._assess_transport_coverage(analysis, bounds)

        features = np.array([
            congestion, ecology, pedestrian, transport,  # 0-3: базові метрики
            road_density, building_density, green_density,  # 4-6: щільності
            area, aspect_ratio,  # 7-8: геометрія
            road_quality, connectivity, green_distribution,  # 9-11: якісні показники
            population_density, economic_indicator,  # 12-13: контекст
            congestion_severity, ecological_deficit,  # 14-15: проблемні індикатори
            intersection_density, green_fragmentation, transport_coverage  # 16-18: додаткові ознаки
        ])

        return features

    def _calculate_intersection_potential(self, roads_data: List[Dict]) -> float:
        if len(roads_data) < 2:
            return 0.0

        intersection_count = 0
        road_segments = []

        for road in roads_data:
            coords = road.get('coordinates', [])
            if len(coords) > 1:
                road_segments.append(coords)

        for i in range(len(road_segments)):
            for j in range(i + 1, len(road_segments)):
                if self._roads_potentially_intersect(road_segments[i], road_segments[j]):
                    intersection_count += 1

        return min(1.0, intersection_count / max(len(roads_data), 1))

    def _roads_potentially_intersect(self, road1_coords: List, road2_coords: List) -> bool:
        if len(road1_coords) < 2 or len(road2_coords) < 2:
            return False

        r1_lats = [coord[0] for coord in road1_coords if len(coord) >= 2]
        r1_lngs = [coord[1] for coord in road1_coords if len(coord) >= 2]
        r2_lats = [coord[0] for coord in road2_coords if len(coord) >= 2]
        r2_lngs = [coord[1] for coord in road2_coords if len(coord) >= 2]

        if not (r1_lats and r1_lngs and r2_lats and r2_lngs):
            return False

        r1_bbox = (min(r1_lats), max(r1_lats), min(r1_lngs), max(r1_lngs))
        r2_bbox = (min(r2_lats), max(r2_lats), min(r2_lngs), max(r2_lngs))

        return (r1_bbox[0] <= r2_bbox[1] and r1_bbox[1] >= r2_bbox[0] and
                r1_bbox[2] <= r2_bbox[3] and r1_bbox[3] >= r2_bbox[2])

    def _calculate_green_fragmentation(self, green_data: List[Dict], bounds: List[List[float]]) -> float:
        if not green_data:
            return 1.0

        total_area = 0
        areas = []

        for green in green_data:
            coords = green.get('coordinates', [])
            if len(coords) > 2:
                area = self._calculate_polygon_area_simple(coords)
                areas.append(area)
                total_area += area

        if not areas or total_area == 0:
            return 1.0

        mean_area = total_area / len(areas)
        fragmentation = 1.0 / (1.0 + mean_area * 1000)

        return min(1.0, fragmentation)

    def _assess_transport_coverage(self, analysis: Dict, bounds: List[List[float]]) -> float:
        transport_stops = analysis.get('public_transport_stops', [])
        if not transport_stops:
            return 0.1

        territory_area = self._calculate_area(bounds)
        coverage_radius = 0.005

        covered_area = len(transport_stops) * (coverage_radius ** 2) * math.pi
        coverage_ratio = min(1.0, covered_area / territory_area)

        return coverage_ratio

    def _calculate_polygon_area_simple(self, coords: List[List[float]]) -> float:
        if len(coords) < 3:
            return 0

        area = 0
        n = len(coords)
        for i in range(n):
            j = (i + 1) % n
            area += coords[i][0] * coords[j][1]
            area -= coords[j][0] * coords[i][1]

        return abs(area) / 2

    def predict_quality(self, analysis: Dict) -> float:
        try:
            self.load_model()

            features = self.extract_comprehensive_features(analysis)

            territory_type = self._identify_territory_type(features)

            territory_fingerprint = self._create_territory_fingerprint(analysis)
            territory_seed = int(territory_fingerprint[:8], 16)
            np.random.seed(territory_seed)

            adapted_weights = self._adapt_weights_for_territory(territory_type)
            original_weights = self.weights.copy()
            self.weights = adapted_weights

            network_output = self._forward_pass_improved(features)

            quality_prediction = self._interpret_network_output_improved(network_output, features, territory_type)

            self.weights = original_weights

            logger.info(
                f"Покращена нейронна мережа передбачила якість {quality_prediction:.2f} для території типу {territory_type}")

            return min(100.0, max(0.0, quality_prediction))

        except Exception as e:
            logger.error(f"Помилка в нейронній мережі: {e}")
            return self._fallback_quality_calculation(analysis)

    def _forward_pass_improved(self, features: np.ndarray) -> np.ndarray:
        activation = features
        activations = [activation]

        for i in range(len(self.hidden_layers)):
            z = np.dot(activation, self.weights[f'W{i}']) + self.weights[f'b{i}']

            z_normalized = (z - np.mean(z)) / (np.std(z) + 1e-8)

            activation = self._leaky_relu(z_normalized)

            dropout_rate = 0.1 - (i * 0.02)
            if np.random.random() < dropout_rate:
                activation *= (1.0 - dropout_rate)

            activations.append(activation)

        final_z = np.dot(activation, self.weights[f'W{len(self.hidden_layers)}']) + self.weights[
            f'b{len(self.hidden_layers)}']

        output = self._softmax(final_z)

        return output

    def _softmax(self, x):
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)

    def _interpret_network_output_improved(self, network_output: np.ndarray, features: np.ndarray,
                                           territory_type: str) -> float:

        current_quality = self._calculate_baseline_quality(features)
        improvements = network_output * 100

        territory_coefficients = self._get_improved_territory_coefficients(territory_type)

        weighted_improvements = improvements * territory_coefficients

        # Бонус за уникнення конфліктів
        conflict_avoidance_bonus = improvements[10] * 5
        integration_bonus = improvements[11] * 3

        total_improvement = (np.sum(weighted_improvements) / len(weighted_improvements) +
                             conflict_avoidance_bonus + integration_bonus)

        if territory_type == 'traffic_heavy':
            max_improvement = 40
        elif territory_type == 'green_residential':
            max_improvement = 25
        else:
            max_improvement = 35

        actual_improvement = min(max_improvement, total_improvement)

        predicted_quality = current_quality + actual_improvement

        return predicted_quality

    def _get_improved_territory_coefficients(self, territory_type: str) -> np.ndarray:
        coefficients = {
            'urban_dense': np.array([0.9, 0.6, 1.0, 0.9, 0.8, 0.5, 0.6, 0.8, 0.9, 0.8, 0.9, 0.8]),
            'suburban': np.array([0.7, 0.8, 0.8, 0.7, 0.8, 0.7, 0.8, 0.9, 0.6, 0.7, 0.8, 0.8]),
            'industrial': np.array([0.8, 1.0, 0.6, 0.7, 0.9, 1.0, 0.8, 0.7, 0.8, 0.9, 0.8, 0.7]),
            'rural': np.array([0.5, 0.9, 0.6, 0.5, 0.6, 0.9, 0.8, 0.8, 0.3, 0.8, 0.7, 0.8]),
            'mixed_residential': np.array([0.7, 0.7, 0.8, 0.7, 0.7, 0.6, 0.7, 0.8, 0.7, 0.7, 0.8, 0.8]),
            'green_residential': np.array([0.6, 0.9, 0.8, 0.6, 0.5, 0.8, 0.7, 0.9, 0.4, 0.9, 0.8, 0.9]),
            'traffic_heavy': np.array([1.0, 0.5, 0.7, 0.9, 0.8, 0.6, 0.7, 0.8, 1.0, 0.6, 0.9, 0.8])
        }

        return coefficients.get(territory_type, coefficients['mixed_residential'])

    def generate_personalized_improvements(self, analysis: Dict) -> Dict:
        try:
            self.load_model()

            features = self.extract_comprehensive_features(analysis)

            territory_type = self._identify_territory_type(features)
            territory_fingerprint = self._create_territory_fingerprint(analysis)

            territory_seed = int(territory_fingerprint[:8], 16)
            np.random.seed(territory_seed)

            adapted_weights = self._adapt_weights_for_territory(territory_type)
            original_weights = self.weights.copy()
            self.weights = adapted_weights

            network_output = self._forward_pass_improved(features)

            improvements = self._generate_improved_specific_improvements(
                network_output, features, territory_type, analysis
            )
            self.weights = original_weights

            logger.info(f"Згенеровані покращені персоналізовані рішення для території типу {territory_type}")

            return improvements

        except Exception as e:
            logger.error(f"Помилка генерації покращень: {e}")
            return self._generate_fallback_improvements(analysis)

    def _generate_improved_specific_improvements(self, network_output: np.ndarray, features: np.ndarray,
                                                 territory_type: str, analysis: Dict) -> Dict:
        traffic_reduction_need = network_output[0]
        ecology_boost_need = network_output[1]
        walkability_need = network_output[2]
        transport_need = network_output[3]
        efficiency_focus = network_output[4]
        sustainability_focus = network_output[5]
        cost_consideration = network_output[6]
        feasibility_score = network_output[7]
        roundabout_need = network_output[8]
        green_separation_need = network_output[9]
        conflict_avoidance_priority = network_output[10]
        integration_quality = network_output[11]

        bounds = analysis.get('bounds', [[50.45, 30.52], [50.44, 30.53]])
        area = self._calculate_area(bounds)

        improvements = {}

        if traffic_reduction_need > 0.6:
            road_count = max(2, min(5, int(traffic_reduction_need * 6)))
            improvements['new_roads'] = road_count
            improvements['road_focus'] = 'traffic_flow'

            if territory_type == 'urban_dense':
                improvements['road_types'] = ['tertiary', 'residential']
                improvements['prefer_underground'] = conflict_avoidance_priority > 0.7
            elif territory_type == 'traffic_heavy':
                improvements['road_types'] = ['primary', 'secondary']
                improvements['bypass_roads'] = True
                improvements['intelligent_signals'] = True
            else:
                improvements['road_types'] = ['secondary', 'tertiary']

            improvements['avoid_green_conflicts'] = green_separation_need > 0.6
            improvements['organic_curves'] = territory_type in ['rural', 'green_residential']
        else:
            improvements['new_roads'] = max(1, int(traffic_reduction_need * 4))
            improvements['road_focus'] = 'connectivity'

        if ecology_boost_need > 0.5:
            green_count = max(2, min(8, int(ecology_boost_need * 8)))
            improvements['green_spaces_count'] = green_count

            if territory_type == 'industrial':
                improvements['green_types'] = ['park', 'forest', 'buffer_zone']
                improvements['air_purification'] = True
                improvements['industrial_buffers'] = True
            elif territory_type == 'urban_dense':
                improvements['green_types'] = ['square', 'pocket_park', 'rooftop_garden']
                improvements['vertical_greening'] = True
                improvements['micro_parks'] = conflict_avoidance_priority > 0.7
            elif territory_type == 'green_residential':
                improvements['green_types'] = ['park', 'meadow', 'community_garden']
                improvements['preserve_existing'] = True
                improvements['green_corridors'] = green_separation_need > 0.6
            else:
                improvements['green_types'] = ['park', 'garden']

            improvements['road_separation_buffer'] = green_separation_need > 0.5
            improvements['no_green_road_overlap'] = True
        else:
            improvements['green_spaces_count'] = max(1, int(ecology_boost_need * 4))
            improvements['green_types'] = ['garden']

        if roundabout_need > 0.6 and territory_type in ['urban_dense', 'traffic_heavy', 'mixed_residential']:
            improvements['roundabouts_needed'] = True
            improvements['roundabout_count'] = min(3, max(1, int(roundabout_need * 4)))

            if territory_type == 'traffic_heavy':
                improvements['roundabout_type'] = 'large'
                improvements['roundabout_priority'] = 'maximum_flow'
            elif territory_type == 'urban_dense':
                improvements['roundabout_type'] = 'compact'
                improvements['roundabout_priority'] = 'space_efficient'
            else:
                improvements['roundabout_type'] = 'standard'
                improvements['roundabout_priority'] = 'balanced'

            improvements['roundabout_logic'] = 'intersection_based'
            improvements['min_roads_for_roundabout'] = 3
        else:
            improvements['roundabouts_needed'] = False

        if transport_need > 0.4:
            stop_count = max(2, min(6, int(transport_need * 7)))
            improvements['transport_stops'] = stop_count