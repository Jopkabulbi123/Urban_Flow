from django.test import TestCase
from backend.services.analysis import AreaAnalyzer
from unittest.mock import patch


class TestIntegration(TestCase):
    @patch('backend.services.osm_data.OSMDataFetcher.get_area_data')
    def test_full_analysis_flow(self, mock_get_data):
        mock_get_data.return_value = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "nodes": [1, 2],
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
                    "lat": 50.001,
                    "lon": 30.001
                },
                {
                    "type": "way",
                    "id": 2,
                    "tags": {
                        "leisure": "park",
                        "name": "Central Park"
                    }
                }
            ]
        }

        analyzer = AreaAnalyzer()
        result = analyzer.perform_analysis(50.1, 29.9, 49.9, 30.1)

        self.assertIn("bounds", result)
        self.assertEqual(result["road_count"], 1)
        self.assertIn("Головні", result["road_types"])
        self.assertGreater(result["ecology"], 10)
        self.assertEqual(len(result["hourly_congestion"]), 24)