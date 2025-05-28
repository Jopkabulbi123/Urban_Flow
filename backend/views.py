from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .forms import CustomUserCreationForm
from backend.services.analysis import AreaAnalyzer


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
    return render(request, 'index.html')


def city_changer_view(request):
    return render(request, 'city_changer.html')