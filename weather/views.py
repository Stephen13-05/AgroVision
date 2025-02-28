from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import requests
from datetime import datetime, timedelta
from .models import WeatherHistory
import json
import traceback

def get_nasa_power_data(lat, lon):
    """Get soil moisture and pH data from NASA POWER API"""
    nasa_power_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Calculate date range (last 7 days to ensure we have data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    params = {
        "parameters": "GWETPROF,GWETROOT,GWETTOP,RH2M,ALLSKY_SFC_PAR_TOT",  # Correct NASA POWER parameters
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Fetching soil data from NASA POWER API: {nasa_power_url}")  # Debug log
        print(f"Parameters: {params}")  # Debug log
        response = requests.get(nasa_power_url, params=params, headers=headers)
        print(f"NASA API response status: {response.status_code}")  # Debug log
        print(f"NASA API response: {response.text[:500]}")  # Debug log first 500 chars
        
        if response.status_code == 200:
            data = response.json()
            
            # Initialize result dictionary
            result = {
                'soil_moisture': None,
                'soil_ph': None
            }
            
            # Get soil moisture from GWETPROF (Root zone soil wetness)
            if 'GWETPROF' in data['properties']['parameter']:
                moisture_data = data['properties']['parameter']['GWETPROF']
                dates = sorted(moisture_data.keys(), reverse=True)
                
                for date in dates:
                    value = moisture_data[date]
                    if value != -999.0 and value is not None:
                        # GWETPROF is already in percentage (0-100)
                        result['soil_moisture'] = round(float(value), 2)
                        break
            
            # If GWETPROF not available, try GWETROOT
            if result['soil_moisture'] is None and 'GWETROOT' in data['properties']['parameter']:
                moisture_data = data['properties']['parameter']['GWETROOT']
                dates = sorted(moisture_data.keys(), reverse=True)
                
                for date in dates:
                    value = moisture_data[date]
                    if value != -999.0 and value is not None:
                        # GWETROOT is already in percentage (0-100)
                        result['soil_moisture'] = round(float(value), 2)
                        break
            
            # Calculate approximate soil pH based on other parameters
            # This is an approximation based on relative humidity and solar radiation
            if 'RH2M' in data['properties']['parameter'] and 'ALLSKY_SFC_PAR_TOT' in data['properties']['parameter']:
                rh_data = data['properties']['parameter']['RH2M']
                par_data = data['properties']['parameter']['ALLSKY_SFC_PAR_TOT']
                dates = sorted(rh_data.keys(), reverse=True)
                
                for date in dates:
                    rh_value = rh_data[date]
                    par_value = par_data[date]
                    if rh_value != -999.0 and par_value != -999.0:
                        # Estimate pH based on environmental factors
                        # Higher humidity and radiation typically correlate with lower pH
                        # This is a simplified approximation
                        rh_factor = rh_value / 100  # normalize to 0-1
                        par_factor = min(par_value / 1000, 1)  # normalize to 0-1
                        
                        # Calculate pH in range 5.5-7.5 (most common soil pH range)
                        estimated_ph = 7.5 - (rh_factor * par_factor * 2)
                        result['soil_ph'] = round(estimated_ph, 2)
                        break
            
            print(f"Soil data retrieved: {result}")  # Debug log
            
            # If any value is still None, use defaults
            if result['soil_moisture'] is None:
                result['soil_moisture'] = 50.0
            if result['soil_ph'] is None:
                result['soil_ph'] = 7.0
                
            return result
            
    except Exception as e:
        print(f"Error fetching soil data: {str(e)}")  # Debug log
        print(f"Full error: {traceback.format_exc()}")  # More detailed error log
    
    # Return default values if no data found
    return {
        'soil_moisture': 50.0,
        'soil_ph': 7.0
    }

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

            # OpenWeather API calls
            api_key = 'ba86488f2ade832395a7ac641beaab67'
            current_weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            
            # Get current weather data
            weather_response = requests.get(current_weather_url)
            forecast_response = requests.get(forecast_url)
            
            print(f"Weather API response status: {weather_response.status_code}")  # Debug log
            print(f"Forecast API response status: {forecast_response.status_code}")  # Debug log
            
            if weather_response.status_code != 200 or forecast_response.status_code != 200:
                return JsonResponse({'status': 'error', 'message': 'Weather API error'})
            
            weather_data = weather_response.json()
            forecast_data = forecast_response.json()
            
            # Get soil moisture and pH from NASA POWER
            print("Fetching soil data")  # Debug log
            soil_data = get_nasa_power_data(lat, lon)
            print(f"Soil data: {soil_data}")  # Debug log

            # Process forecast data to get daily forecasts
            daily_forecasts = []
            seen_dates = set()
            
            for item in forecast_data['list']:
                date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                if date not in seen_dates and len(daily_forecasts) < 8:
                    seen_dates.add(date)
                    daily_forecasts.append({
                        'date': date,
                        'temperature': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': item['wind']['speed'],
                        'precipitation': item.get('rain', {}).get('3h', 0),
                        'weather_condition': item['weather'][0]['main'],
                        'description': item['weather'][0]['description'],
                        'icon': item['weather'][0]['icon']
                    })

            weather_info = {
                'current': {
                    'temperature': weather_data['main']['temp'],
                    'humidity': weather_data['main']['humidity'],
                    'wind_speed': weather_data['wind']['speed'],
                    'precipitation': weather_data.get('rain', {}).get('1h', 0),
                    'weather_condition': weather_data['weather'][0]['main'],
                    'description': weather_data['weather'][0]['description'],
                    'icon': weather_data['weather'][0]['icon'],
                    'location_name': weather_data['name'],
                    'soil_moisture': soil_data['soil_moisture'],
                    'soil_ph': soil_data['soil_ph']
                },
                'forecast': daily_forecasts
            }
            
            # Save to history
            try:
                WeatherHistory.objects.create(
                    latitude=lat,
                    longitude=lon,
                    temperature=weather_info['current']['temperature'],
                    humidity=weather_info['current']['humidity'],
                    wind_speed=weather_info['current']['wind_speed'],
                    precipitation=weather_info['current']['precipitation'],
                    weather_condition=weather_info['current']['weather_condition'],
                    soil_moisture=weather_info['current']['soil_moisture'],
                    soil_ph=weather_info['current']['soil_ph'],
                    location_name=weather_info['current']['location_name']
                )
            except Exception as e:
                print(f"Error saving to history: {str(e)}")  # Debug log
            
            return JsonResponse({'status': 'success', 'data': weather_info})
            
        except Exception as e:
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
        'soil_moisture': [],
        'soil_ph': []
    }
    
    for record in reversed(list(history)):
        history_data['dates'].append(record.date.strftime('%Y-%m-%d %H:%M'))
        history_data['temperatures'].append(float(record.temperature))
        history_data['humidity'].append(float(record.humidity))
        history_data['soil_moisture'].append(float(record.soil_moisture))
        history_data['soil_ph'].append(float(record.soil_ph))
    
    context = {
        'history': history,
        'history_data_json': json.dumps(history_data)  # Serialize the data here
    }
    return render(request, 'weather/dashboard.html', context)
