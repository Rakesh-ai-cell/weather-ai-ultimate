import os
import requests
import google.generativeai as genai
from django.shortcuts import render
from datetime import datetime
import base64
from io import BytesIO
from gtts import gTTS

# Configure Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def index(request):
    api_key = os.environ.get('WEATHER_API_KEY')
    weather_data = {}
    
    if 'history' not in request.session:
        request.session['history'] = []

    if request.method == 'POST' or request.GET.get('city'):
        query = request.POST.get('city') or request.GET.get('city')
        is_slow = request.POST.get('speed') == 'slow'
        
        try:
            # Geocoding
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={api_key}"
            geo_res = requests.get(geo_url).json()

            if geo_res:
                lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
                display_name = f"{geo_res[0]['name']}, {geo_res[0]['country']}"

                # Fetch Weather
                curr_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
                curr_res = requests.get(curr_url).json()

                # AI Voice Logic
                ai_insight = "Fetching AI weather tip..."
                audio_base64 = ""
                try:
                    prompt = f"Give a witty 1-line weather tip for {display_name} where it is {curr_res['main']['temp']}°C."
                    ai_insight = model.generate_content(prompt).text.strip()
                    tts = gTTS(text=ai_insight, lang='en', slow=is_slow)
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    audio_base64 = base64.b64encode(fp.getvalue()).decode('utf-8')
                except: pass

                weather_data = {
                    'city': display_name,
                    'temp': round(curr_res['main']['temp']),
                    'desc': curr_res['weather'][0]['description'],
                    'icon': curr_res['weather'][0]['icon'],
                    'ai_insight': ai_insight,
                    'audio_data': audio_base64,
                }
        except Exception as e:
            print(f"Error: {e}")

    return render(request, 'index.html', {'weather': weather_data})