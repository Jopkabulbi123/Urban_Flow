from django.db import models
from django.contrib.auth.models import User


class AnalyzedArea(models.Model):
    """Model for storing analyzed geographic areas"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    north = models.FloatField()
    south = models.FloatField()
    east = models.FloatField()
    west = models.FloatField()
    area = models.FloatField(help_text="Area in square kilometers")
    created_at = models.DateTimeField(auto_now_add=True)

    road_count = models.IntegerField(default=0)
    congestion = models.IntegerField(default=0, help_text="Congestion score (0-100)")
    ecology = models.IntegerField(default=0, help_text="Ecology score (0-100)")
    pedestrian_friendly = models.IntegerField(default=0, help_text="Pedestrian friendliness score (0-100)")
    public_transport = models.IntegerField(default=0, help_text="Public transport accessibility score (0-100)")

    def __str__(self):
        return f"Area {self.id}: [{self.north}, {self.west}] to [{self.south}, {self.east}]"

    class Meta:
        verbose_name = "Analyzed Area"
        verbose_name_plural = "Analyzed Areas"


class Road(models.Model):
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='roads')
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255, default="Unnamed road")
    road_type = models.CharField(max_length=50)
    length = models.FloatField(help_text="Length in kilometers")

    def __str__(self):
        return f"{self.name} ({self.road_type})"

    class Meta:
        verbose_name = "Road"
        verbose_name_plural = "Roads"


class RoadTypeStats(models.Model):
    """Statistics about types of roads in an area"""
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='road_type_stats')
    road_type = models.CharField(max_length=50)
    count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.road_type}: {self.count}"


class HourlyCongestion(models.Model):
    """Hourly congestion data for an area"""
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='hourly_congestion')
    hour = models.IntegerField()
    congestion_level = models.IntegerField(help_text="Congestion level (0-100)")

    def __str__(self):
        return f"Hour {self.hour}: {self.congestion_level}%"

    class Meta:
        ordering = ['hour']


class GreenSpace(models.Model):
    """Green spaces in an analyzed area"""
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='green_spaces')
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255, default="Unnamed green space")
    space_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.space_type})"


class WaterFeature(models.Model):
    """Water features in an analyzed area"""
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='water_features')
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255, default="Unnamed water feature")
    feature_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.feature_type})"