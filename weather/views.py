from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import requests
from datetime import datetime, timedelta
from .models import WeatherHistory
import json

def get_nasa_power_data(lat, lon):
    """Get soil moisture data from NASA POWER API"""
    nasa_power_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "SOIL_M",  # Changed from SOIL_M_0_10CM to SOIL_M
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
        "end": datetime.now().strftime("%Y%m%d"),
        "format": "JSON"
    }
    
    try:
        print(f"Fetching soil data from NASA POWER API: {nasa_power_url}")  # Debug log
        response = requests.get(nasa_power_url, params=params)
        print(f"NASA API response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            data = response.json()
            # Get the most recent date's data
            dates = list(data['properties']['parameter']['SOIL_M'].keys())
            if dates:
                latest_date = dates[-1]
                soil_moisture = data['properties']['parameter']['SOIL_M'][latest_date]
                return round(float(soil_moisture), 2)
    except Exception as e:
        print(f"Error fetching soil moisture: {str(e)}")  # Debug log
    return 35.0  # Return a default value if unable to get real data

def get_coordinates_from_city(city_name):
    """Get coordinates from city name using OpenWeather Geocoding API"""
    api_key = 'ba86488f2ade832395a7ac641beaab67'
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
    
    try:
        response = requests.get(geocoding_url)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'latitude': data[0]['lat'],
                    'longitude': data[0]['lon']
                }
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def get_weather_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lon = data.get('longitude')
            city = data.get('city')

            print(f"Received data: city={city}, lat={lat}, lon={lon}")  # Debug log

            # If city is provided, get coordinates
            if city and not (lat and lon):
                print(f"Getting coordinates for city: {city}")  # Debug log
                coords = get_coordinates_from_city(city)
                if coords:
                    lat = coords['latitude']
                    lon = coords['longitude']
                    print(f"Found coordinates: lat={lat}, lon={lon}")  # Debug log
                else:
                    print("City not found in geocoding")  # Debug log
                    return JsonResponse({'status': 'error', 'message': 'City not found'})

            if not (lat and lon):
                print("Missing location information")  # Debug log
                return JsonResponse({'status': 'error', 'message': 'Location information missing'})

            # OpenWeather API call
            api_key = 'ba86488f2ade832395a7ac641beaab67'
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            print(f"Fetching weather data from: {weather_url}")  # Debug log
            
            # Get weather data
            weather_response = requests.get(weather_url)
            print(f"Weather API response status: {weather_response.status_code}")  # Debug log
            
            if weather_response.status_code != 200:
                print(f"Weather API error: {weather_response.text}")  # Debug log
                return JsonResponse({'status': 'error', 'message': f'Weather API error: {weather_response.text}'})
            
            weather_data = weather_response.json()
            
            # Get soil moisture from NASA POWER
            print("Fetching soil moisture data")  # Debug log
            soil_moisture = get_nasa_power_data(lat, lon)
            print(f"Soil moisture data: {soil_moisture}")  # Debug log
            
            if weather_response.status_code == 200:
                weather_info = {
                    'temperature': weather_data['main']['temp'],
                    'humidity': weather_data['main']['humidity'],
                    'wind_speed': weather_data['wind']['speed'],
                    'precipitation': weather_data.get('rain', {}).get('1h', 0),
                    'weather_condition': weather_data['weather'][0]['main'],
                    'location_name': weather_data['name'],
                    'soil_moisture': soil_moisture or 0,
                }
                
                # Save to history
                try:
                    WeatherHistory.objects.create(
                        latitude=lat,
                        longitude=lon,
                        **weather_info
                    )
                except Exception as e:
                    print(f"Error saving to history: {str(e)}")  # Debug log
                
                return JsonResponse({'status': 'success', 'data': weather_info})
            
        except Exception as e:
            import traceback
            print(f"Error in get_weather_data: {str(e)}")  # Debug log
            print(traceback.format_exc())  # Print full traceback
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def weather_dashboard(request):
    # Get last 7 days of weather history
    history = WeatherHistory.objects.all().order_by('-date')[:7]
    
    # Prepare history data for the chart
    history_data = {
        'dates': [],
        'temperatures': [],
        'humidity': [],
        'soil_moisture': []
    }
    
    for record in reversed(list(history)):
        history_data['dates'].append(record.date.strftime('%Y-%m-%d %H:%M'))
        history_data['temperatures'].append(float(record.temperature))
        history_data['humidity'].append(float(record.humidity))
        history_data['soil_moisture'].append(float(record.soil_moisture))
    
    context = {
        'history': history,
        'history_data_json': json.dumps(history_data)  # Serialize the data here
    }
    return render(request, 'weather/dashboard.html', context)
