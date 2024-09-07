"""паттерны Flyweight и Proxy + расчет спиральной траектории"""
import time
import math
import matplotlib.pyplot as plt
#import airsim
import numpy as np
import asyncio
import logging
import cv2
from app_api_abc import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CoordinateFlyweight:    # Паттерн Flyweight для управления координатами
    _coordinates = {}

    @staticmethod
    def get_coordinate(lat, lon):
        key = (lat, lon)
        if key not in CoordinateFlyweight._coordinates:  # если координаты еще не сохранены
            CoordinateFlyweight._coordinates[key] = key  # добавляет их в хранилище
                                                # Возвращается ссылка на существующие или вновь созданные координаты
        return CoordinateFlyweight._coordinates[key]

class DJIDroneProxy:          # Паттерн Proxy для управления доступа методами дрона
    def __init__(self, current_drone):
        self._currentl_drone = current_drone

    def global_position_control(self, lat=None, lon=None, alt=None):
        # Логирование запроса на перемещение
        logging.info(f"Запрос на перемещение к широте: {lat}, долготе: {lon}, высоте: {alt}")
        # Обращаемся к реальному дрону через его SDK
        self._currentl_drone.global_position_control(lat, lon, alt)
        # Задержка для симуляции выполнения операции
        # time.sleep(1)

    def connect(self):
        logging.info("Запрос на подключение к дрону через SDK")
        self._currentl_drone.request_sdk_permission_control()

    def takeoff(self):
        logging.info("Взлет инициирован")
        self._currentl_drone.takeoff()

    def land(self):
        logging.info("Посадка инициирована")
        self._currentl_drone.land()


class AirSimAPI():     # Класс, реализующий API для работы с AirSim

    def global_position_control(self, lat=None, lon=None, alt=None):
        print(f"Перемещение к широте: {lat}, долготе: {lon}, высоте: {alt}")

    """async def global_position_control(client: airsim.MultirotorClient, lat=None, lon=None, alt=None):
        waypoint = airsim.Vector3r(lat, lon, alt)
        velosity = 5  # скорость дрона
        client.moveToPositionAsync(waypoint.x_val, waypoint.y_val, waypoint.z_val, velosity).join()
        await land(client)  # вызов функции для приземления

    def request_sdk_permission_control(self):
        self.client = airsim.MultirotorClient()  # попытка подключения
        self.client.confirmConnection()          # Подтверждение соединения с симулятором
        logging.info("Подключение через Air Sim")

    async def get_image(self, max_attempts=10, delay=1):
        # Запрос изображения с камеры 0
        responses = self.client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
        if responses:
            response = responses[0]
            # Преобразование изображения из байтового буфера в RGB-изображение
            img_1D = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
            img_rgb = img_1D.reshape(response.height, response.width, 3)
            # Сохранение изображения на диск
            cv2.imwrite('test.jpg', img_rgb)
            print("Image saved")
        else:
            print("No images found")"""

    async def get_telemetry(client):
        while True:
            state = client.getMultirotorState()
            position = state.kinematics_estimated.position
            velocity = state.kinematics_estimated.linear_velocity
            info_state = f"""
            Позиция дрона: 
                x = {position.x_val:.2f}, y = {position.y_val:.2f}, z = {position.z_val:.2f}
            Скорость дрона (м/с):
                x = {velocity.x_val:.2f}, y = {velocity.y_val:.2f}, z = {velocity.z_val:.2f}
            """
            logging.info(info_state)
            await asyncio.sleep(1)

    def takeoff(self):
        print("Выполняем взлет")

    def land(self, client):
        alt = client.getMultirotorState().kinematics_estimated.position.z_val
        logging.info(f"Текущая высота: {alt} метров")
        velosity = 5  # скорость дрона
        if alt < -5:
            logging.info("Высота выше 5 метров, начинаем снижение до 5 метров...")
            client.moveToPositionAsync(0, 0, -5, velosity).join()  # снижение до 5 метров
            time.sleep(1)  # зависает на 2 сек

        logging.info("Начинаем посадку...")
        client.landAsync().join()  # приземление


class DroneAPIFactory:      # Фабрика для создания объектов  API
    @staticmethod
    def get_drone_api(type_api, connect_uri="http://127.0.0.1:5000"):
        if type_api == "AirSim":
            return AirSimAPI()
        else:
            raise ValueError("Такое API не реализовано")


""""# Возврат на исходную точку
drone.global_position_control(begin_lat, begin_lon, alt=altitude)
time.sleep(2)
drone.land()"""


