from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('city-changer/', views.city_changer_view, name='city_changer'),
    path('api/analyze/', views.analyze_area, name='analyze_area'),
]