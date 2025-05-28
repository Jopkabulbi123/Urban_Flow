import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from backend.services.analysis import AreaAnalyzer


class TestAreaAnalyzer(TestCase):
    def setUp(self):
        self.analyzer = AreaAnalyzer()

        self.sample_osm_data = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "nodes": [1, 2, 3],
                    "tags": {
                        "highway": "primary",
                        "name": "Main Street"
                    }
                },
                {
                    "type": "node",
                    "id": 1,
                    "lat": 50.0,
                    "lon": 30.0
                },
                {
                    "type": "node",
                    "id": 2,
                    "lat": 50.1,
                    "lon": 30.1
                },
                {
                    "type": "node",
                    "id": 3,
                    "lat": 50.2,
                    "lon": 30.2
                },
                {
                    "type": "way",
                    "id": 2,
                    "tags": {
                        "leisure": "park",
                        "name": "Central Park"
                    }
                },
                {
                    "type": "node",
                    "id": 4,
                    "tags": {
                        "public_transport": "stop_position"
                    }
                }
            ]
        }

    @patch('backend.services.analysis.OSMDataFetcher.get_area_data')
    def test_perform_analysis(self, mock_get_data):
        mock_get_data.return_value = self.sample_osm_data

        result = self.analyzer.perform_analysis(50.5, 29.5, 49.5, 30.5)

        self.assertIn("bounds", result)
        self.assertIn("road_count", result)
        self.assertIn("ecology", result)
        self.assertEqual(result["road_count"], 1)

    def test_calculate_area_size(self):
        area = self.analyzer._calculate_area_size(50.5, 29.5, 49.5, 30.5)
        self.assertGreater(area, 0)
        self.assertLess(area, 10000)

    def test_extract_road_data(self):
        roads, count, types = self.analyzer._extract_road_data(self.sample_osm_data)
        self.assertEqual(count, 1)
        self.assertIn("Головні", types)
        self.assertEqual(len(roads), 1)
        self.assertGreater(roads[0]["length"], 0)

    def test_extract_green_and_water_data(self):
        green, water = self.analyzer._extract_green_and_water_data(self.sample_osm_data)
        self.assertEqual(len(green), 1)
        self.assertEqual(len(water), 0)

    def test_calculate_score(self):
        self.assertEqual(self.analyzer._calculate_score(5, 10), 50)
        self.assertEqual(self.analyzer._calculate_score(1, 1, 100), 95)
        self.assertEqual(self.analyzer._calculate_score(0, 1), 10)

    def test_find_longest_road(self):
        roads = [
            {"name": "Road 1", "length": 5},
            {"name": "Unnamed road", "length": 10},
            {"name": "Road 2", "length": 7}
        ]
        longest = self.analyzer._find_longest_road(roads)
        self.assertEqual(longest["name"], "Road 2")
        self.assertEqual(longest["length"], 7)

        unnamed_roads = [
            {"name": "Unnamed road", "length": 10},
            {"name": "Unnamed road", "length": 5}
        ]
        longest = self.analyzer._find_longest_road(unnamed_roads)
        self.assertEqual(longest["name"], "Unnamed road")
        self.assertEqual(longest["length"], 10)