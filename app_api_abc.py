"""Абстрактный интерфейс для создания API дрона"""
from abc import ABC, abstractmethod

class IDroneAPI(ABC):
    def __init__(self, connect_uri=None):
        self.client = None              # Переменная для хранения клиента API
        self.connect_uri = connect_uri  # URI для подключения к дрону, если требуется

    @abstractmethod
    def request_sdk_permission_control(self):
        """Метод для подключения к SDK."""
        pass

    @abstractmethod
    def get_image(self, max_attempts=10, delay=1):  # количество попыток и задержка(1сек)
        """Метод для получения изображения с камеры дрона. """
        pass
