from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .models import AnalyzedArea, Road, RoadTypeStats, HourlyCongestion, GreenSpace, WaterFeature
from .forms import CustomUserCreationForm
from backend.services.analysis import AreaAnalyzer
from django.shortcuts import get_object_or_404


@login_required
def my_projects(request):
    projects = request.user.analyzedarea_set.all()
    return render(request, 'projects/myprojects.html', {
        'has_projects': projects.exists(),
        'projects': projects
    })


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(AnalyzedArea, id=project_id, user=request.user)

    hourly_congestion = project.hourly_congestion.all().order_by('hour')

    print(f"Project ID: {project.id}")
    print(f"Hourly congestion count: {hourly_congestion.count()}")
    for hc in hourly_congestion:
        print(f"Hour {hc.hour}: {hc.congestion_level}%")

    context = {
        'project': project,
        'hourly_congestion': hourly_congestion,
        'roads': project.roads.all(),
        'green_spaces': project.green_spaces.all(),
        'water_features': project.water_features.all(),
        'road_type_stats': project.road_type_stats.all()
    }

    return render(request, 'projects/project_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_area(request):
    try:
        data = json.loads(request.body)
        analyzer = AreaAnalyzer()

        nw_lat = float(data['nw_lat'])
        nw_lng = float(data['nw_lng'])
        se_lat = float(data['se_lat'])
        se_lng = float(data['se_lng'])

        results = analyzer.perform_analysis(nw_lat, nw_lng, se_lat, se_lng)

        return JsonResponse({
            'status': 'success',
            'results': results
        })

    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid coordinate values: {str(e)}'
        }, status=400)
    except KeyError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Missing required field: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }, status=500)


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Реєстрація успішна!')
            return redirect('profile')
        else:
            print("Форма не валідна:", form.errors)
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('profile')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    return render(request, 'registration/profile.html', {'user': request.user})


def home_view(request):
    if request.user.is_authenticated:
        return redirect('logged_home')
    return render(request, 'index.html')


@login_required
def logged_home_view(request):
    projects_count = request.user.analyzedarea_set.count()
    return render(request, 'index_logged.html', {
        'projects_count': projects_count
    })


def city_changer_view(request):
    return render(request, 'city_changer.html')

def about_view(request):
    return render(request, 'about.html')


@login_required
@require_http_methods(["POST"])
def save_project(request):
    try:
        data = json.loads(request.body)

        analyzer = AreaAnalyzer()
        nw_lat, nw_lng = map(float, data['nw_coords'].split(','))
        se_lat, se_lng = map(float, data['se_coords'].split(','))

        analysis_results = analyzer.perform_analysis(nw_lat, nw_lng, se_lat, se_lng)

        project = AnalyzedArea.objects.create(
            user=request.user,
            north=analysis_results['bounds'][0][0],
            south=analysis_results['bounds'][1][0],
            east=analysis_results['bounds'][1][1],
            west=analysis_results['bounds'][0][1],
            area=analysis_results['area'],
            road_count=analysis_results['road_count'],
            congestion=analysis_results['congestion'],
            ecology=analysis_results['ecology'],
            pedestrian_friendly=analysis_results['pedestrian_friendly'],
            public_transport=analysis_results['public_transport']
        )

        for road_type, count in analysis_results['road_types'].items():
            RoadTypeStats.objects.create(
                area=project,
                road_type=road_type,
                count=count
            )

        hourly_congestion_data = analysis_results.get('hourly_congestion', [])
        print(f"Saving hourly congestion data: {hourly_congestion_data}")

        for hour, level in enumerate(hourly_congestion_data):
            HourlyCongestion.objects.create(
                area=project,
                hour=hour,
                congestion_level=level
            )
            print(f"Created HourlyCongestion: hour={hour}, level={level}")

        for road in analysis_results.get('roads_data', []):
            Road.objects.create(
                area=project,
                osm_id=road['id'],
                name=road['name'],
                road_type=road['type'],
                length=road['length']
            )

        for space in analysis_results.get('green_spaces_data', []):
            GreenSpace.objects.create(
                area=project,
                osm_id=space['id'],
                name=space['name'],
                space_type=space['type']
            )

        for water in analysis_results.get('water_features_data', []):
            WaterFeature.objects.create(
                area=project,
                osm_id=water['id'],
                name=water['name'],
                feature_type=water['type']
            )

        return JsonResponse({
            'status': 'success',
            'project_id': project.id
        })

    except Exception as e:
        print(f"Error saving project: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_project(request, project_id):
    try:
        project = AnalyzedArea.objects.get(id=project_id, user=request.user)
        project.delete()
        return JsonResponse({'status': 'success'})
    except AnalyzedArea.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Проєкт не знайдено'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)