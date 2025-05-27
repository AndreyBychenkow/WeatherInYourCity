#🐍 WeatherForecast (Flask)

![](https://i.postimg.cc/NGSY5K9q/obsh.jpg)

## 📌 Описание проекта

WeatherForecast — это современное Flask-приложение для просмотра текущей погоды и прогноза на 7 дней по любому городу мира. Интерфейс на русском языке, с автодополнением городов, историей поиска и глобальной статистикой по популярности городов.

## 📌 Установка и настройка

### 🔧 Предварительные требования:

- Python 3.10 или выше
- СУБД по вашему выбору
- Виртуальное окружение (рекомендуется)

1. 📌 **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/AndreyBychenkow/WeatherInYourCity.git
   ```
2. 📌 **Установите зависимости:**

   ```bash
   pip install -r requirements.txt   
   ```
### 🚀 Запуск локально (без Docker)

```sh
python app.py
```
Откройте http://localhost:5000

### 🚀 Запуск Docker (рекомендуется)

```sh
docker build -t weather-forecast .
docker run -p 5000:5000 weather-forecast
```

Откройте http://localhost:5000

### ⏳ Тестирование

```sh
pytest -v
```
**Тесты не требуют интернета — все внешние API замоканы**


## ✅ Реализовано:

- Поиск города с автодополнением (подсказки через Nominatim)

![](https://i.postimg.cc/B6JkV1hy/image.jpg)

- Получение текущей погоды и прогноза на 7 дней (Open-Meteo API)

![](https://i.postimg.cc/qvkm0dch/7-day.jpg)

- Предложение последнего города при повторном заходе

![](https://i.postimg.cc/RVCfZC8B/image.jpg)

- Глобальная статистика по городам (API `/api/city_stats`)

![](https://i.postimg.cc/nzt9bn7N/image.jpg)

- Тесты (pytest, с моками внешних API)

![](https://i.postimg.cc/Nf09wJ9G/image.jpg)

- Docker-контейнеризация

![](https://i.postimg.cc/nrhzprLS/debug.jpg)

## Технологии
- **Python 3.12**
- **Flask** — веб-фреймворк
- **requests** — HTTP-запросы к внешним API
- **pytest** — тестирование
- **Docker** — контейнеризация
- **Nominatim** (OpenStreetMap) — геокодинг городов
- **Open-Meteo** — погодный API

## Структура
- `app.py` — основной код приложения (Flask, логика, API)
- `test_app.py` — тесты (pytest, unittest.mock)
- `requirements.txt` — зависимости
- `Dockerfile`, `.dockerignore` — контейнеризация
- `README.md` —  инструкция по запуску проекта

