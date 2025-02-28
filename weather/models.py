from django.db import models
from django.utils import timezone

# Create your models here.

class WeatherHistory(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)
    precipitation = models.DecimalField(max_digits=5, decimal_places=2)
    weather_condition = models.CharField(max_length=50)
    soil_moisture = models.DecimalField(max_digits=5, decimal_places=2)
    soil_ph = models.DecimalField(max_digits=4, decimal_places=2, default=7.0)  # pH scale is 0-14
    location_name = models.CharField(max_length=100)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.location_name} - {self.date}"
