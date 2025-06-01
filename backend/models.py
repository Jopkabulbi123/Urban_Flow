from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class AnalyzedArea(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    north = models.FloatField()
    south = models.FloatField()
    east = models.FloatField()
    west = models.FloatField()
    related_name = 'analyzedarea_set'
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

    def save(self, *args, **kwargs):
        from backend.services.analysis import haversine
        avg_latitude = (self.north + self.south) / 2
        width_km = haversine(self.west, avg_latitude, self.east, avg_latitude)
        height_km = haversine(self.west, self.north, self.west, self.south)
        self.area = round(width_km * height_km, 2)
        super().save(*args, **kwargs)


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
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='road_type_stats')
    road_type = models.CharField(max_length=50)
    count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.road_type}: {self.count}"


class HourlyCongestion(models.Model):
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='hourly_congestion')
    hour = models.IntegerField()  # Година доби (0-23)
    congestion_level = models.IntegerField(help_text="Congestion level (0-100)")

    def __str__(self):
        return f"Hour {self.hour}: {self.congestion_level}%"

    class Meta:
        ordering = ['hour']


class GreenSpace(models.Model):
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='green_spaces')
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255, default="Unnamed green space")
    space_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.space_type})"


class WaterFeature(models.Model):
    area = models.ForeignKey(AnalyzedArea, on_delete=models.CASCADE, related_name='water_features')
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=255, default="Unnamed water feature")
    feature_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.feature_type})"