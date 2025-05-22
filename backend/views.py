from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import logging
from .services.analysis import AreaAnalyzer

logger = logging.getLogger(__name__)


def home_view(request):
    return render(request, 'index.html')


def city_changer_view(request):
    return render(request, 'city_changer.html')


@csrf_exempt
def analyze_area(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Метод не підтримується. Використовуйте POST.'
        }, status=405)

    try:
        data = json.loads(request.body)

        required_fields = ['nw_lat', 'nw_lng', 'se_lat', 'se_lng']
        if not all(field in data for field in required_fields):
            return HttpResponseBadRequest(
                'Відсутні обов\'язкові поля: nw_lat, nw_lng, se_lat, se_lng'
            )

        analyzer = AreaAnalyzer()
        results = analyzer.perform_analysis(
            float(data['nw_lat']),
            float(data['nw_lng']),
            float(data['se_lat']),
            float(data['se_lng'])
        )

        return JsonResponse({
            'status': 'success',
            'results': results
        })

    except ValueError as e:
        logger.error(f"Помилка валідації координат: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f"Невірний формат координат: {str(e)}"
        }, status=400)

    except Exception as e:
        logger.error(f"Помилка під час аналізу: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f"Внутрішня помилка сервера: {str(e)}"
        }, status=500)