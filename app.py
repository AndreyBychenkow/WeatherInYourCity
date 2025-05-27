from flask import Flask, render_template_string, request, make_response
import requests
from datetime import datetime
import json
import threading
import os

app = Flask(__name__)

WEATHER_CODES = {
    0: 'Ясно',
    1: 'Преимущественно ясно',
    2: 'Переменная облачность',
    3: 'Пасмурно',
    45: 'Туман',
    48: 'Инейный туман',
    51: 'Морось слабая',
    53: 'Морось',
    55: 'Морось сильная',
    56: 'Ледяная морось слабая',
    57: 'Ледяная морось сильная',
    61: 'Дождь слабый',
    63: 'Дождь',
    65: 'Дождь сильный',
    66: 'Ледяной дождь слабый',
    67: 'Ледяной дождь сильный',
    71: 'Снег слабый',
    73: 'Снег',
    75: 'Снег сильный',
    77: 'Снежные зерна',
    80: 'Ливень слабый',
    81: 'Ливень',
    82: 'Ливень сильный',
    85: 'Снегопад слабый',
    86: 'Снегопад сильный',
    95: 'Гроза',
    96: 'Гроза с градом слабая',
    99: 'Гроза с градом сильная',
}

HTML = '''
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Прогноз погоды</title>
  <style>
    body {
      background: linear-gradient(120deg, #e0eafc 0%, #cfdef3 100%);
      font-family: 'Segoe UI', Arial, sans-serif;
      margin: 0;
      padding: 0;
      min-height: 100vh;
    }
    .container {
      max-width: 700px;
      margin: 40px auto;
      background: #fff;
      border-radius: 18px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.10);
      padding: 32px 40px 40px 40px;
      position: relative;
    }
    .weather-img {
      display: block;
      margin: 0 auto 18px auto;
      width: 120px;
      filter: drop-shadow(0 2px 8px #b3c6e0);
    }
    h1 {
      text-align: center;
      font-size: 2.5em;
      margin-bottom: 18px;
      font-weight: 700;
      color: #2a3a5a;
    }
    form {
      display: flex;
      justify-content: center;
      margin-bottom: 24px;
      gap: 8px;
      position: relative;
    }
    #suggestions {
      position: absolute;
      left: 0;
      top: 100%;
      min-width: 220px;
      max-width: 350px;
      z-index: 10;
    }
    input[name="city"] {
      padding: 8px 14px;
      border: 1px solid #b3c6e0;
      border-radius: 6px;
      font-size: 1em;
      outline: none;
      transition: border 0.2s;
    }
    input[name="city"]:focus {
      border: 1.5px solid #4a90e2;
    }
    input[type="submit"] {
      background: #4a90e2;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 8px 18px;
      font-size: 1em;
      cursor: pointer;
      font-weight: 600;
      transition: background 0.2s;
    }
    input[type="submit"]:hover {
      background: #357ab8;
    }
    h2 {
      color: #2a3a5a;
      margin-top: 32px;
      margin-bottom: 10px;
    }
    ul {
      font-size: 1.1em;
      margin-bottom: 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: #f7faff;
      border-radius: 8px;
      overflow: hidden;
    }
    th, td {
      padding: 10px 8px;
      text-align: center;
    }
    th {
      background: #e0eafc;
      color: #2a3a5a;
      font-weight: 600;
      font-size: 1.05em;
    }
    tr:nth-child(even) {
      background: #f0f4fa;
    }
    tr:nth-child(odd) {
      background: #f7faff;
    }
    .error {
      color: #d32f2f;
      text-align: center;
      font-weight: 600;
      margin-bottom: 18px;
    }
  </style>
</head>
<body>
  <div class="container">
    <img class="weather-img" src="https://cdn-icons-png.flaticon.com/512/1163/1163661.png" alt="Погода">
    <h1>Узнай погоду в своём городе</h1>
    <form method="post">
      <input name="city" placeholder="Введите город" required autocomplete="off" id="city-input" style="min-width:220px;max-width:350px;width:100%;">
      <div id="suggestions"></div>
      <input type="submit" value="Показать погоду">
    </form>
    {% if show_last_city and last_city and not city %}
      <div style="text-align:center;margin:18px 0 0 0;">
        <button id="show-last-city" style="background:#e0eafc;color:#2a3a5a;border:none;border-radius:6px;padding:8px 18px;font-size:1em;cursor:pointer;font-weight:600;">Показать погоду в {{ last_city }}</button>
      </div>
      <script>
        document.getElementById('show-last-city').onclick = function(e) {
          e.preventDefault();
          const form = document.createElement('form');
          form.method = 'POST';
          form.style.display = 'none';
          const input = document.createElement('input');
          input.name = 'city';
          input.value = {{ last_city|tojson }};
          form.appendChild(input);
          document.body.appendChild(form);
          form.submit();
        };
      </script>
    {% endif %}
    <script>
      const input = document.getElementById('city-input');
      const suggestionsBox = document.getElementById('suggestions');
      let timer = null;
      input.addEventListener('input', function() {
        clearTimeout(timer);
        const val = this.value.trim();
        if (!val) {
          suggestionsBox.innerHTML = '';
          return;
        }
        timer = setTimeout(() => {
          fetch(`/autocomplete?q=${encodeURIComponent(val)}`)
            .then(r => r.json())
            .then(data => {
              if (!data.suggestions.length) {
                suggestionsBox.innerHTML = '';
                return;
              }
              suggestionsBox.innerHTML = '<div style="background:#fff;border:1px solid #b3c6e0;border-radius:0 0 6px 6px;box-shadow:0 2px 8px #b3c6e0;margin-top:2px;width:100%;">' +
                data.suggestions.map(s => `<div style='padding:7px 12px;cursor:pointer;' class='sugg-item'>${s}</div>`).join('') + '</div>';
              Array.from(document.getElementsByClassName('sugg-item')).forEach(el => {
                el.onclick = () => {
                  input.value = el.textContent;
                  suggestionsBox.innerHTML = '';
                };
              });
            });
        }, 200);
      });
      document.addEventListener('click', function(e) {
        if (!suggestionsBox.contains(e.target) && e.target !== input) {
          suggestionsBox.innerHTML = '';
        }
      });
    </script>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    {% if weather %}
      <h2>Погода в {{ city }}:</h2>
      <ul>
        <li>Температура: {{ weather['temperature'] }}°C</li>
        <li>Погода: {{ weather['description'] }}</li>
      </ul>
    {% endif %}
    {% if forecast %}
      <h2>Прогноз на 7 дней:</h2>
      <table>
        <tr><th>Дата</th><th>Мин, °C</th><th>Макс, °C</th><th>Погода</th></tr>
        {% for day in forecast %}
          <tr>
            <td>{{ day['date'] }}</td>
            <td>{{ day['min'] }}</td>
            <td>{{ day['max'] }}</td>
            <td>{{ day['desc'] }}</td>
          </tr>
        {% endfor %}
      </table>
    {% endif %}
  </div>
</body>
</html>
'''

STATS_FILE = 'city_stats.json'
stats_lock = threading.Lock()

def update_city_stats(city):
    city_norm = city.strip().lower()
    with stats_lock:
        stats = {}
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            except Exception:
                stats = {}
        stats[city_norm] = stats.get(city_norm, 0) + 1
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False)

def get_city_stats():
    with stats_lock:
        if not os.path.exists(STATS_FILE):
            return {}
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

def get_coords(city):
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    resp = requests.get(url, params=params, headers={"User-Agent": "weather-app"})
    data = resp.json()
    if not data:
        return None, None
    return float(data[0]['lat']), float(data[0]['lon'])

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "auto"
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if 'current_weather' not in data:
        return None, None
    weather = data['current_weather']
    code = weather['weathercode']
    desc = WEATHER_CODES.get(code, f"Код {code}")
    forecast = []
    if 'daily' in data:
        daily = data['daily']
        for i in range(len(daily['time'])):
            code = daily['weathercode'][i]
            date_fmt = datetime.strptime(daily['time'][i], "%Y-%m-%d").strftime("%d.%m.%Y")
            forecast.append({
                'date': date_fmt,
                'min': daily['temperature_2m_min'][i],
                'max': daily['temperature_2m_max'][i],
                'desc': WEATHER_CODES.get(code, f"Код {code}")
            })
    return {
        'temperature': weather['temperature'],
        'description': desc
    }, forecast

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    error = None
    forecast = None
    city = ''
    last_city = request.cookies.get('last_city', '')
    show_last_city = False
    if request.method == 'POST':
        city = request.form['city']
        lat, lon = get_coords(city)
        if lat is None:
            error = 'Город не найден!'
        else:
            weather, forecast = get_weather(lat, lon)
            if not weather:
                error = 'Не удалось получить погоду.'
        resp = make_response(render_template_string(HTML, weather=weather, error=error, city=city, forecast=forecast, last_city=last_city, show_last_city=show_last_city))
        if city and not error:
            resp.set_cookie('last_city', city, max_age=60*60*24*30)
            # --- История поиска ---
            history = []
            try:
                history = json.loads(request.cookies.get('search_history', '[]'))
            except Exception:
                history = []
            city_norm = city.strip().lower()
            history = [c for c in history if c != city_norm]
            history.insert(0, city_norm)
            history = history[:10]
            resp.set_cookie('search_history', json.dumps(history, ensure_ascii=False), max_age=60*60*24*30)
            # --- Глобальная статистика ---
            update_city_stats(city)
        return resp
    # GET
    if last_city:
        show_last_city = True
    return render_template_string(HTML, weather=weather, error=error, city=city, forecast=forecast, last_city=last_city, show_last_city=show_last_city)

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '')
    if not query:
        return {"suggestions": []}
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 5, "addressdetails": 1}
    resp = requests.get(url, params=params, headers={"User-Agent": "weather-app"})
    data = resp.json()
    suggestions = []
    for item in data:
        name = item.get('display_name')
        if name:
            suggestions.append(name)
    return {"suggestions": suggestions}

@app.route('/api/city_stats')
def api_city_stats():
    return get_city_stats()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True) 