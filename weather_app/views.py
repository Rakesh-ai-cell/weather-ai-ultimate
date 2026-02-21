import os
import requests
import google.generativeai as genai
from django.shortcuts import render
from datetime import datetime
import base64
from io import BytesIO
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

# Setup Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def index(request):
    api_key = os.getenv('WEATHER_API_KEY')
    if 'history' not in request.session:
        request.session['history'] = []

    weather_data = {}

    if request.method == 'POST' or request.GET.get('city'):
        query = request.POST.get('city') or request.GET.get('city')
        is_slow = request.POST.get('speed') == 'slow'
        
        # 1. Geocoding
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={api_key}"
        geo_res = requests.get(geo_url).json()

        if geo_res and len(geo_res) > 0:
            lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
            display_name = f"{geo_res[0]['name']}, {geo_res[0]['country']}"

            # 2. Fetch Data (FIXED: No .json() inside requests.get)
            curr_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
            fore_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
            
            curr_res = requests.get(curr_url).json()
            fore_res = requests.get(fore_url).json()

            # 3. History Sidebar
            history = request.session['history']
            if display_name not in history:
                history.insert(0, display_name)
                request.session['history'] = history[:6]
                request.session.modified = True
            
            # 4. Forecast & Chart
            forecast_list, chart_temps, chart_labels = [], [], []
            for item in fore_res['list'][::8]:
                dt = datetime.fromtimestamp(item['dt'])
                day = dt.strftime('%a')
                forecast_list.append({'day': day, 'temp': round(item['main']['temp']), 'icon': item['weather'][0]['icon']})
                chart_temps.append(round(item['main']['temp']))
                chart_labels.append(day)

            # 5. AI Voice Synthesis
            ai_insight = "Dashboard ready."
            audio_base64 = ""
            try:
                prompt = f"Give a witty 2-line weather tip for {display_name}. Temp: {curr_res['main']['temp']}°C."
                ai_insight = model.generate_content(prompt).text.strip()
                
                tts = gTTS(text=ai_insight, lang='en', slow=is_slow)
                fp = BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            except: pass

            weather_data = {
                'city': display_name,
                'temp': round(curr_res['main']['temp']),
                'desc': curr_res['weather'][0]['description'],
                'icon': curr_res['weather'][0]['icon'],
                'humidity': curr_res['main']['humidity'],
                'wind': curr_res['wind']['speed'],
                'pressure': curr_res['main']['pressure'],
                'visibility': round(curr_res.get('visibility', 0)/1000, 1),
                'sunrise': datetime.fromtimestamp(curr_res['sys']['sunrise']).strftime('%I:%M %p'),
                'sunset': datetime.fromtimestamp(curr_res['sys']['sunset']).strftime('%I:%M %p'),
                'ai_insight': ai_insight,
                'audio_data': audio_base64,
                'is_slow': is_slow,
                'bbox': f"{lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}",
                'marker': f"{lat},{lon}",
                'chart_temps': chart_temps,
                'chart_labels': chart_labels,
                'forecast': forecast_list
            }

    return render(request, 'index.html', {'weather': weather_data, 'history': request.session['history']})