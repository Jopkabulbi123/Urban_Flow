from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/analyze/', views.analyze_area, name='analyze_area'),
]