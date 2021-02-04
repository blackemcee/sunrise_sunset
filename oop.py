"""
Учебный проект для определения времени восхода/захода солнца в указанном
месте в указанный день. Можно указать широту и долготу, а можно название
места (в этом случае широта и долгота определяются автоматически).
Если указаны и название, и координаты - введенные координаты будут
проигнорированы и вычислены автоматически.

Для тестирования работы программы необходимо:
1. Создать объект класса Place, на вход передать либо название места
в произвольном виде (name='имя_места'), либо координаты (latitude=XXX,
longitude=YYY).
2. Создать объект класса Times. На вход ничего не передавать (если нас
интересует текущая дата), либо передать дату в формате ДД.ММ.ГГГГ
(date='DD.MM.YYYY').
3. Для объекта Times вызвать метод show_result, в качестве параметра
передать объект класса Place.
"""

import json
import requests
import datetime as dt
from geopy.geocoders import Nominatim
from tzwhere import tzwhere
import pytz

API_URL = 'https://api.sunrise-sunset.org/json'
DATE_FORMAT = '%d.%m.%Y'
TIME_FORMAT = '%H:%M'
# colors
WARNING = '\033[91m'
OKGREEN = '\033[92m'
ENDC = '\033[0m'


class Place:
    """
    Класс для места, для которого мы ходим узнать время восхода/заката
    """

    def __init__(self, name=None, latitude=None, longitude=None):
        if name is not None:
            if latitude is not None or longitude is not None:
                print(f'{WARNING}Вы явно ввели название места, поэтому '
                      f'координаты '
                      f'будут '
                      f'вычислены автоматически{ENDC}')
            location = Nominatim(
                user_agent="yuriy.kirillov@gmail.com").geocode(name)
            self.name = location
            self.latitude = location.latitude
            self.longitude = location.longitude
        else:
            # если название не введено, проверяем, что введеты
            # полные координаты
            if latitude is None or longitude is None:
                print(f'{WARNING}Данных недостаточно. Введите место или его '
                      f'координаты{ENDC}')
                raise ValueError
            else:
                self.latitude, self.longitude = latitude, longitude
            # строка для финального вывода
            self.name = f'с координатами {self.latitude}, {self.longitude}'

    def timezone(self):
        """
        Вычисляем timezone для заданных координат
        """
        timezwhere = tzwhere.tzwhere()
        return timezwhere.tzNameAt(self.latitude, self.longitude)


class Times:
    """
       Основной класс для вычисления времени восхода и заката. На вход
       принимает объект класса Place
    """
    def __init__(self, date='today'):
        if date == 'today':
            self.entered_date = dt.date.today()
        else:
            self.entered_date = dt.datetime.strptime(date, DATE_FORMAT).date()

    def get_times(self, place):
        # Метод для отправки запроса на сервер времени и полечения
        # времен рассвета и заката
        request_params = {
            'lat': place.latitude,
            'lng': place.longitude,
            'date': self.entered_date,
            'formatted': 0
        }
        response = requests.get(API_URL, params=request_params)
        # ответ приходит в виде json, поэтому используем json.loads
        # для превращения его в словарь
        json_data_full = json.loads(response.text)
        sunrise_str, sunset_str = (json_data_full['results']['sunrise'],
                                   json_data_full['results']['sunset'])
        # Получили время в стринге, переводим в datetime
        # ВАЖНО: это время в UTC
        sunrise_utc = dt.datetime.strptime(sunrise_str,
                                           '%Y-%m-%dT%H:%M:%S%z')
        sunset_utc = dt.datetime.strptime(sunset_str, '%Y-%m-%dT%H:%M:%S%z')
        return [sunrise_utc, sunset_utc]

    def apply_timezone(self, place):
        # Нам необходимо перевести время из UTC в часовой пояс
        # запрошенного места

        # берем таймзону нашего места в формате timezone
        tz = pytz.timezone(place.timezone())
        # переводим время рассвета и заката с utc на нашу timezone
        sunrise_local = self.get_times(place)[0].astimezone(tz)
        sunset_local = self.get_times(place)[1].astimezone(tz)
        return [sunrise_local, sunset_local]

    def show_result(self, place):
        # Метод для вывода результата
        sunrise = self.apply_timezone(place)[0].strftime(TIME_FORMAT)
        sunset = self.apply_timezone(place)[1].strftime(TIME_FORMAT)
        date = self.entered_date.strftime(DATE_FORMAT)
        print(f'Вы запросили информацию для региона {OKGREEN}{place.name}'
              f'{ENDC}')
        if 'координатами' not in place.name:
            print(f'Широта: {place.latitude}, долгота: {place.longitude}')
        print('-----------------------')
        print(f'В день {OKGREEN}{date}{ENDC} солнце встанет в '
              f'{OKGREEN}{sunrise}{ENDC}, а сядет в {OKGREEN}{sunset}{ENDC}')
