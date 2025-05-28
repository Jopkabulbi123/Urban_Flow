import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from backend.services.osm_data import OSMDataFetcher, haversine


class TestHaversine(unittest.TestCase):
    def test_haversine(self):
        # Київ - Львів (приблизно)
        distance = haversine(30.5234, 50.4501, 24.0297, 49.8397)
        self.assertAlmostEqual(distance, 469, delta=10)  # ~469 км


class TestOSMDataFetcher(TestCase):
    @patch('backend.services.osm_data.requests.post')
    def test_get_area_data_success(self, mock_post):
        # Налаштовуємо mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"elements": [{"type": "node", "id": 1}]}
        mock_post.return_value = mock_response

        fetcher = OSMDataFetcher()
        result = fetcher.get_area_data(50, 30, 49, 31)

        self.assertEqual(result, {"elements": [{"type": "node", "id": 1}]})
        mock_post.assert_called_once()

    @patch('backend.services.osm_data.requests.post')
    def test_get_area_data_rate_limit(self, mock_post):
        # Перший виклик повертає 429, другий - успішний
        mock_response1 = MagicMock()
        mock_response1.status_code = 429

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"elements": []}

        mock_post.side_effect = [mock_response1, mock_response2]

        fetcher = OSMDataFetcher()
        result = fetcher.get_area_data(50, 30, 49, 31)

        self.assertEqual(result, {"elements": []})
        self.assertEqual(mock_post.call_count, 2)

    @patch('backend.services.osm_data.requests.post')
    def test_get_area_data_error(self, mock_post):
        mock_post.side_effect = Exception("API Error")

        fetcher = OSMDataFetcher()
        result = fetcher.get_area_data(50, 30, 49, 31)

        self.assertEqual(result, {"elements": []})