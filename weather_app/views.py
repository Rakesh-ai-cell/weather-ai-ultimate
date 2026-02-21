
import os
import requests
import google.generativeai as genai
from django.shortcuts import render
from datetime import datetime
import base64
from io import BytesIO
from gtts import gTTS

# Configure AI
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def index(request):
    api_key = os.environ.get('WEATHER_API_KEY')
    weather_data = {}
    forecast_list = []

    if request.method == 'POST' or request.GET.get('city'):
        query = request.POST.get('city') or request.GET.get('city')
        
        try:
            # 1. Get Coordinates
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={api_key}"
            geo_data = requests.get(geo_url).json()

            if geo_data:
                lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
                city_full_name = f"{geo_data[0]['name']}, {geo_data[0]['country']}"

                # 2. Get Current Weather
                curr_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
                curr_res = requests.get(curr_url).json()

                # 3. Get 5-Day Forecast (This fixes the week names)
                fore_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
                fore_res = requests.get(fore_url).json()

                # Filter to get one forecast per day (approx noon)
                for item in fore_res['list']:
                    if "12:00:00" in item['dt_txt']:
                        dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
                        forecast_list.append({
                            'day': dt.strftime('%A'), # Monday, Tuesday, etc.
                            'temp': round(item['main']['temp']),
                            'icon': item['weather'][0]['icon'],
                            'desc': item['weather'][0]['description']
                        })

                # 4. AI Insight & Voice
                ai_insight = "Clear skies today!"
                audio_base64 = ""
                try:
                    prompt = f"Give a witty 1-line weather tip for {city_full_name} ({curr_res['weather'][0]['description']}, {round(curr_res['main']['temp'])}°C)."
                    ai_insight = model.generate_content(prompt).text.strip()
                    tts = gTTS(text=ai_insight, lang='en')
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    audio_base64 = base64.b64encode(fp.getvalue()).decode('utf-8')
                except: pass

                weather_data = {
                    'city': city_full_name,
                    'temp': round(curr_res['main']['temp']),
                    'desc': curr_res['weather'][0]['description'],
                    'icon': curr_res['weather'][0]['icon'],
                    'ai_insight': ai_insight,
                    'audio_data': audio_base64,
                }
        except Exception as e:
            print(f"Error: {e}")

    return render(request, 'index.html', {'weather': weather_data, 'forecast': forecast_list})