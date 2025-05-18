from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from services.analysis import AreaAnalyzer
import logging

logger = logging.getLogger(__name__)

from django.shortcuts import render

def home_page(request):
    return render(request, 'index.html')


@csrf_exempt
def analyze_area(request):
    if request.method == 'POST':
        try:
            # Get data from request body
            data = json.loads(request.body)

            # Input validation
            required_fields = ['nw_lat', 'nw_lng', 'se_lat', 'se_lng']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Missing required field: {field}'
                    }, status=400)

            # Perform analysis
            analyzer = AreaAnalyzer()
            results = analyzer.perform_analysis(
                float(data.get('nw_lat')),
                float(data.get('nw_lng')),
                float(data.get('se_lat')),
                float(data.get('se_lng'))
            )

            return JsonResponse({
                'status': 'success',
                'results': results
            })
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid coordinate format: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Error during area analysis: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method allowed'
    }, status=405)