import random
import time
import json
import os
from typing import List, Dict, Tuple
from ..osm_data import OSMDataFetcher, haversine


class OSMTrainingDataCollector:
    def __init__(self):
        self.osm_fetcher = OSMDataFetcher()
        self.data_file = os.path.join(os.path.dirname(__file__), 'data', 'training_data.json')
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

        self.regions = {
            'north_america': ((-125, 24), (-66, 50)),
            'europe': ((-10, 35), (40, 60)),
            'east_asia': ((70, 20), (140, 50)),
            'japan': ((129, 31), (146, 45)),
            'australia': ((113, -44), (154, -10))
        }

    def generate_random_location(self, region_bbox: Tuple[Tuple[float, float], Tuple[float, float]]) -> Tuple[float, float, float, float]:
        west, south = region_bbox[0]
        east, north = region_bbox[1]

        center_lat = south + random.random() * (north - south)
        center_lon = west + random.random() * (east - west)

        # Менший розмір для простоти
        side_km = 1 + random.random() * 2
        side_deg = side_km / 111.32

        nw_lat = center_lat + side_deg / 2
        nw_lon = center_lon - side_deg / 2
        se_lat = center_lat - side_deg / 2
        se_lon = center_lon + side_deg / 2

        return nw_lat, nw_lon, se_lat, se_lon

    def is_mostly_land(self, bbox: Tuple[float, float, float, float]) -> bool:
        nw_lat, nw_lon, se_lat, se_lon = bbox
        width = haversine(nw_lon, nw_lat, se_lon, nw_lat)
        height = haversine(nw_lon, nw_lat, nw_lon, se_lat)
        area = width * height
        return area <= 20  # Зменшили для простоти

    def collect_training_data(self, num_samples: int = 1000):  # Менше зразків
        training_data = []

        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    training_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                training_data = []

        regions_list = list(self.regions.values())
        collected_count = len(training_data)

        while collected_count < num_samples:
            try:
                region = random.choice(regions_list)
                bbox = self.generate_random_location(region)

                if not self.is_mostly_land(bbox):
                    continue

                nw_lat, nw_lon, se_lat, se_lon = bbox
                osm_data = self.osm_fetcher.get_area_data(nw_lat, nw_lon, se_lat, se_lon)

                if not osm_data or 'elements' not in osm_data or len(osm_data['elements']) < 5:  # Менший поріг
                    continue

                # Спрощені дані для тренування
                training_sample = {
                    'bbox': bbox,
                    'simple_metrics': {
                        'road_count': len([e for e in osm_data['elements'] if e.get('type') == 'way' and 'highway' in e.get('tags', {})]),
                        'green_count': len([e for e in osm_data['elements'] if e.get('type') == 'way' and e.get('tags', {}).get('leisure') in ['park', 'garden']]),
                        'building_count': len([e for e in osm_data['elements'] if e.get('type') == 'way' and 'building' in e.get('tags', {})]),
                        'total_elements': len(osm_data['elements'])
                    }
                }

                training_data.append(training_sample)
                collected_count += 1

                if collected_count % 50 == 0:
                    with open(self.data_file, 'w') as f:
                        json.dump(training_data, f, indent=2)
                    print(f"Зібрано {collected_count} зразків")

                time.sleep(0.2)

            except Exception as e:
                print(f"Помилка при зборі даних: {e}")
                time.sleep(0.5)
                continue

        with open(self.data_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        print(f"Збір даних завершено. Всього зразків: {collected_count}")


class TrainingDataProcessor:
    def __init__(self, data_file=None):
        if data_file is None:
            data_file = os.path.join(os.path.dirname(__file__), 'data', 'training_data.json')
        self.data_file = data_file

    def load_data(self):
        if not os.path.exists(self.data_file):
            return []

        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def get_statistics(self):
        data = self.load_data()
        if not data:
            return {"total_samples": 0}

        stats = {
            "total_samples": len(data),
            "avg_roads": sum(d['simple_metrics'].get('road_count', 0) for d in data) / len(data),
            "avg_green": sum(d['simple_metrics'].get('green_count', 0) for d in data) / len(data),
            "avg_buildings": sum(d['simple_metrics'].get('building_count', 0) for d in data) / len(data)
        }
        return stats

    def filter_by_region(self, region_name):
        data = self.load_data()
        if region_name not in OSMTrainingDataCollector().regions:
            return data

        region_bbox = OSMTrainingDataCollector().regions[region_name]
        filtered = []

        for sample in data:
            bbox = sample['bbox']
            nw_lat, nw_lon, se_lat, se_lon = bbox
            center_lat = (nw_lat + se_lat) / 2
            center_lon = (nw_lon + se_lon) / 2

            west, south = region_bbox[0]
            east, north = region_bbox[1]

            if (west <= center_lon <= east) and (south <= center_lat <= north):
                filtered.append(sample)

        return filtered


if __name__ == "__main__":
    collector = OSMTrainingDataCollector()
    collector.collect_training_data(num_samples=50)

    processor = TrainingDataProcessor()
    stats = processor.get_statistics()
    print(f"Статистика: {stats}")