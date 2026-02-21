
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
        # Get speed from form for voice
        is_slow = request.POST.get('speed') == 'slow'
        
        try:
            # 1. Coordinates
            geo_res = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={api_key}").json()

            if geo_res:
                lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
                city_name = f"{geo_res[0]['name']}, {geo_res[0]['country']}"

                # 2. Current Weather
                curr_res = requests.get(f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}").json()

                # 3. 5-Day Forecast
                fore_res = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}").json()
                for item in fore_res['list']:
                    if "12:00:00" in item['dt_txt']:
                        dt = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
                        forecast_list.append({
                            'day': dt.strftime('%A'),
                            'temp': round(item['main']['temp']),
                            'icon': item['weather'][0]['icon'],
                            'desc': item['weather'][0]['description']
                        })

                # 4. AI Voice & Insight
                ai_insight = "Fetching AI weather tip..."
                audio_base = ""
                try:
                    prompt = f"Give a witty 1-line weather tip for {city_name} where it is {curr_res['main']['temp']}°C."
                    ai_insight = model.generate_content(prompt).text.strip()
                    tts = gTTS(text=ai_insight, lang='en', slow=is_slow)
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    audio_base = base64.b64encode(fp.getvalue()).decode('utf-8')
                except: pass

                weather_data = {
                    'city': city_name,
                    'temp': round(curr_res['main']['temp']),
                    'desc': curr_res['weather'][0]['description'],
                    'icon': curr_res['weather'][0]['icon'],
                    'humidity': curr_res['main']['humidity'],
                    'wind': curr_res['wind']['speed'],
                    'pressure': curr_res['main']['pressure'],
                    'visibility': curr_res.get('visibility', 0) / 1000,
                    'ai_insight': ai_insight,
                    'audio': audio_base,
                    'lat': lat,
                    'lon': lon
                }
        except Exception as e: print(e)

    return render(request, 'index.html', {'weather': weather_data, 'forecast': forecast_list})