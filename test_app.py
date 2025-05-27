import os
import json
import tempfile
import pytest
from app import app, STATS_FILE
from unittest.mock import patch

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    # Мокаем файл статистики
    orig_stats_file = STATS_FILE
    app.STATS_FILE = db_path
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.remove(db_path)
    app.STATS_FILE = orig_stats_file

class FakeResp:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data

def fake_nominatim_get(url, params=None, headers=None):
    # Для Москвы и Парижа возвращаем координаты
    q = params.get('q', '').lower()
    if 'москва' in q:
        return FakeResp([{'lat': '55.7558', 'lon': '37.6173', 'display_name': 'Москва, Россия'}])
    if 'париж' in q:
        return FakeResp([{'lat': '48.8534951', 'lon': '2.3483915', 'display_name': 'Париж, Франция'}])
    return FakeResp([])

def fake_openmeteo_get(url, params=None, **kwargs):
    # Возвращаем фейковую погоду
    lat = float(params['latitude'])
    if abs(lat - 55.7558) < 0.01:
        city = 'Москва'
    elif abs(lat - 48.8534951) < 0.01:
        city = 'Париж'
    else:
        city = 'Unknown'
    return FakeResp({
        'current_weather': {'temperature': 20, 'weathercode': 1},
        'daily': {
            'time': ['2024-06-25'],
            'temperature_2m_min': [15],
            'temperature_2m_max': [25],
            'weathercode': [1]
        }
    })

@patch('app.requests.get', side_effect=lambda url, **kwargs: fake_nominatim_get(url, **kwargs) if 'nominatim' in url else fake_openmeteo_get(url, **kwargs))
def test_city_search_success(mock_get, client):
    resp = client.post('/', data={'city': 'Москва'})
    assert resp.status_code == 200
    text = resp.data.decode('utf-8')
    assert 'Погода в' in text
    assert 'Москва' in text
    # Проверяем куки
    cookies = resp.headers.get_all('Set-Cookie')
    assert any('last_city' in c for c in cookies)
    assert any('search_history' in c for c in cookies)

@patch('app.requests.get', side_effect=lambda url, **kwargs: fake_nominatim_get(url, **kwargs) if 'nominatim' in url else fake_openmeteo_get(url, **kwargs))
def test_city_search_fail(mock_get, client):
    resp = client.post('/', data={'city': 'ГородКоторогоНет123'})
    assert resp.status_code == 200
    assert 'Город не найден' in resp.data.decode('utf-8')

@patch('app.requests.get', side_effect=lambda url, **kwargs: fake_nominatim_get(url, **kwargs) if 'nominatim' in url else fake_openmeteo_get(url, **kwargs))
def test_city_stats_api(mock_get, client):
    client.post('/', data={'city': 'Москва'})
    client.post('/', data={'city': 'Москва'})
    client.post('/', data={'city': 'Париж'})
    resp = client.get('/api/city_stats')
    assert resp.status_code == 200
    stats = resp.get_json()
    assert stats['москва'] >= 2
    assert stats['париж'] >= 1 