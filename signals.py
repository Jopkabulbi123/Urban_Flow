from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AnalyzedArea

@receiver(post_save, sender=AnalyzedArea)
def analyze_area_handler(sender, instance, created, **kwargs):
    if created:
        print(f"New area analyzed: {instance.id}")