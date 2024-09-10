"""паттерны Flyweight и Factory """
import time
import airsim
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


class AirSimAPI(IDroneAPI):     # Класс, реализующий API для работы с AirSim
    def request_sdk_permission_control(self):
        self.client = airsim.MultirotorClient()  # попытка подключения
        self.client.confirmConnection()          # Подтверждение соединения с симулятором
        logging.info("Подключение через Air Sim")

    def get_image(self, max_attempts=10, delay=1):
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
            print("No images found")

def get_telemetry(client):
    while True:
        state = client.getMultirotorState()
        position = state.kinematics_estimated.position
        velocity = state.kinematics_estimated.linear_velocity
        info_state = f"""
        Позиция дрона:
            x = {position.x_val:.2f}, y = {position.y_val:.2f}, z = {position.z_val:.2f}
        Скорость дрона (м/с):
            x = {velocity.x_val:.2f}, y = {velocity.y_val:.2f}, z = {velocity.z_val:.2f}"""

        logging.info(info_state)
        asyncio.sleep(1)

async def global_position_control(client: airsim.MultirotorClient, lat=None, lon=None, alt=None):
    waypoint = airsim.Vector3r(lat, lon, alt)
    velosity = 5  # скорость дрона
    client.moveToPositionAsync(waypoint.x_val, waypoint.y_val, waypoint.z_val, velosity).join()
    await landed(client)  # вызов функции для приземления

async def landed(client):
    alt = client.getMultirotorState().kinematics_estimated.position.z_val
    logging.info(f"Текущая высота: {alt} метров")
    velosity = 5  # скорость дрона
    if alt < -5:
        logging.info("Высота выше 5 метров, начинаем снижение до 5 метров...")
        client.moveToPositionAsync(0, 0, -5, velosity).join()  # снижение до 5 метров
        time.sleep(2)  # зависает на 2 сек
    logging.info("Начинаем посадку...")
    client.landAsync().join()  # приземление


class DroneAPIFactory:      # Фабрика для создания объектов API
    @staticmethod
    def get_drone_api(type_api):
        if type_api == "AirSim":
            return AirSimAPI()
        else:
            raise ValueError("Такое API не реализовано")