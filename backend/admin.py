from django.contrib import admin
from .models import AnalyzedArea, Road, RoadTypeStats, HourlyCongestion, GreenSpace, WaterFeature

@admin.register(AnalyzedArea)
class AnalyzedAreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'area', 'created_at')
    list_filter = ('created_at',)

@admin.register(Road)
class RoadAdmin(admin.ModelAdmin):
    list_display = ('name', 'road_type', 'length', 'area')
    search_fields = ('name',)

@admin.register(GreenSpace)
class GreenSpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'space_type', 'area')

admin.site.register(RoadTypeStats)
admin.site.register(HourlyCongestion)
admin.site.register(WaterFeature)