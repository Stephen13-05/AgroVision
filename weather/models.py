from django.db import models
from django.utils import timezone

# Create your models here.

class WeatherHistory(models.Model):
    date = models.DateTimeField(default=timezone.now)
    temperature = models.FloatField()
    humidity = models.FloatField()
    wind_speed = models.FloatField()
    precipitation = models.FloatField()
    soil_moisture = models.FloatField()
    weather_condition = models.CharField(max_length=100)
    location_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Weather at {self.location_name} on {self.date.strftime('%Y-%m-%d %H:%M')}"
