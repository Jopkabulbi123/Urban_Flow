from django.test import TestCase, RequestFactory
from django.http import JsonResponse
import json
from backend.views import analyze_area
from unittest.mock import patch


class TestViews(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('backend.views.AreaAnalyzer')
    def test_analyze_area_success(self, mock_analyzer):
        # Налаштовуємо mock
        mock_instance = mock_analyzer.return_value
        mock_instance.perform_analysis.return_value = {"test": "data"}

        # Створюємо POST запит з JSON даними
        data = {
            "nw_lat": 50.5,
            "nw_lng": 29.5,
            "se_lat": 49.5,
            "se_lng": 30.5
        }
        request = self.factory.post(
            '/api/analyze/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = analyze_area(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content), {
            "status": "success",
            "results": {"test": "data"}
        })

    def test_analyze_area_invalid_method(self):
        request = self.factory.get('/api/analyze/')
        response = analyze_area(request)

        self.assertEqual(response.status_code, 405)
        self.assertIn("Метод не підтримується", str(response.content))

    def test_analyze_area_missing_fields(self):
        data = {"nw_lat": 50.5}  # Відсутні інші поля
        request = self.factory.post(
            '/api/analyze/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = analyze_area(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Відсутні обов'язкові поля", str(response.content))

    @patch('backend.views.AreaAnalyzer')
    def test_analyze_area_invalid_coordinates(self, mock_analyzer):
        mock_instance = mock_analyzer.return_value
        mock_instance.perform_analysis.side_effect = ValueError("Invalid coords")

        data = {
            "nw_lat": "invalid",
            "nw_lng": 29.5,
            "se_lat": 49.5,
            "se_lng": 30.5
        }
        request = self.factory.post(
            '/api/analyze/',
            data=json.dumps(data),
            content_type='application/json'
        )

        response = analyze_area(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Невірний формат координат", str(response.content))