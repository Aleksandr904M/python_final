import math
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from functools import wraps
import logging
from app_coordinates_od import *
from app_object_detection import *
from app_flight import *


logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
app = Flask(__name__)
authorization = False
current_drone = {
    "id": "",
    "model": "",
    "manufactured": ""
}
data_from_drones = {
    "start_lat": 0, "start_lon": 0,
    "end_lat": 0, "end_lon": 0,
    "step": 0,
    "altitude": 0
}
coordinates = []

def get_db_connection():  # подключение к БД
    connect = sqlite3.connect('database.db')
    connect.row_factory = sqlite3.Row  # режим получения результатов запросов в виде словаря
    return connect        # возвращает объект подключения

def init_db():
    connect = get_db_connection()  # создание соединения к БД
    connect.execute('CREATE TABLE IF NOT EXISTS users '  # создание таблички если ее нет
                    '(user TEXT NOT NULL, password TEXT NOT NULL)')
    connect.execute('CREATE TABLE IF NOT EXISTS drones '  # создание таблички если ее нет
                    '(id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT NOT NULL, manufactured TEXT NOT NULL)')
    connect.close()

def login_required(func):   # декоратор для защиты, если пользователь не авторизован
    @wraps(func)
    def decorated_function(*args, **kwargs):
        global authorization
        if not authorization:
            return redirect(url_for('login'))  # Перенаправляем на страницу логина, если не авторизован
        return func(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():            # авторизация юзера на главной странице
    if request.method == 'POST':
        connect = get_db_connection()        # соединение
        user = request.form['user']          # получить юзера
        password = request.form['password']  # получить пароль
        user_correct = connect.execute('SELECT * FROM users WHERE user = ?', (user,)).fetchone()  # запрос юзера
        if user_correct:                     # если юзер найден
            user_password = dict(user_correct).get('password')  # преобразовать в словарь, забрать пароль
            if user_password == password:    # если пароль совпал
                global authorization
                authorization = True         # авторизация пройдена
                connect.close()
                return render_template('main.html')
    return render_template('index.html')

@app.route('/<int:drone_id>', methods=['GET', 'POST'])
@login_required
def get_drone(drone_id):         # получает данные по drone_id, выбирает дрон
    connect = get_db_connection()
    if request.method == 'POST':
        result = dict(connect.execute('SELECT * FROM drones WHERE id = ?', (drone_id, )).fetchone())
        current_drone["id"] = drone_id
        current_drone["model"] = result.get("model")
        current_drone["manufactured"] = result.get("manufactured")
        return redirect(url_for('main_window'))
    # запрашивается из базы данных по айдишнику и берется одна строка функцией fetchone()
    drone = connect.execute('SELECT * FROM drones WHERE id = ?', (drone_id,)).fetchone()
    connect.close()
    # рендерит HTML-шаблон и передает туда полученный пост
    return render_template('post.html', drone=drone)

@app.route('/new_user', methods=['GET', 'POST'])
@login_required
def new_post():                    # POST создает нового юзера и записывает в таблицу
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute('INSERT INTO users (user, password) VALUES (?, ?)', (user, password))
        conn.commit()
        conn.close()
        return redirect(url_for('main_window'))
    return render_template('add_post.html')

@app.route('/new_drone', methods=['GET', 'POST'])
@login_required
def new_drone():                   # POST создает нового дрона и записывает в таблицу
    if request.method == 'POST':
        model = request.form['model']
        manufactured = request.form['manufactured']

        conn = get_db_connection()
        conn.execute('INSERT INTO drones (model, manufactured) VALUES (?, ?)', (model, manufactured))
        conn.commit()
        conn.close()
        return redirect(url_for('main_window'))
    return render_template('add_drone.html')

@app.route('/choice_drone', methods=['GET'])
@login_required
def choice_drone():                # печатает список дронов
    conn = get_db_connection()
    drones = conn.execute('SELECT * FROM drones').fetchall()
    conn.close()
    return render_template('choice_drone.html', drones=drones)

@app.route('/missions', methods=['GET', 'POST'])
@login_required
def missions():                    # окно миссий и ввод данных для полета
    if request.method == 'POST':
        try:
            data_from_drones["start_lat"] = float(request.form['start_lat'])
            data_from_drones["start_lon"] = float(request.form['start_lon'])
            data_from_drones["end_lat"] = float(request.form['end_lat'])
            data_from_drones["end_lon"] = float(request.form['end_lon'])
            data_from_drones["step"] = float(request.form['step'])
            data_from_drones["altitude"] = float(request.form["altitude"])
        except Exception:
            return redirect(url_for('error_value'))
    return render_template('missions.html',
                           current_drone=current_drone, data_from_drones=data_from_drones)

@app.route('/mission_spiral', methods=['GET'])
@login_required
def mission_spiral():
    for value in data_from_drones.values():
        if not value:
            return redirect(url_for('error_value'))
    for value in current_drone.values():
        if not value:
            return redirect(url_for('error_value'))
    else:
        drone_api = DroneAPIFactory.get_drone_api("AirSim")
        client = airsim.MultirotorClient()
        main_begin(client, drone_api)
        logging.info(spiral_search(drone_api, client, start_lat=data_from_drones["start_lat"],
                                   start_lon=data_from_drones["start_lon"], end_lat=data_from_drones["end_lat"],
                                   end_lon=data_from_drones["end_lon"], step=data_from_drones["step"],
                                   altitude=data_from_drones["altitude"]))
        return render_template('message_human.html', data="Миссия окончена")

@app.route('/error_value', methods=['GET',])
@login_required
def error_value():
    return render_template('error_value.html')

@app.route('/message_human', methods=['GET',])
@login_required
def message_human():
    return render_template('message_human')

@app.route('/main_window', methods=['GET', 'POST'])
@login_required
def main_window():                 # главное окно
    return render_template('main.html', current_drone=current_drone)

with app.app_context():  # перед первым запросом к базе данных
    init_db()            # Инициализировать базу данных

def object_detection(photo, lat_current, lon_current):  # обнаружение объекта
    obj = ObjectDetection()
    img, detect_objects = obj.detect_objects(photo)
    if detect_objects:
        logging.info("Обнаружены объекты")
        for odj in detect_objects:
            logging.info(f"Класс: {odj["class"]}, вероятность {odj["confidence"]*100:.0f}, координаты {odj["coordinates"]}")
            h_object = 1.70  # данные для расчета
            altitude_drone = data_from_drones["altitude"]
            theta_vertical = -30
            theta_horizontal = 0
            fov_vertical = 45
            fov_horizontal = 60
            w_image = img.shape[1]
            h_image = img.shape[0]
            x1, y1, x2, y2 = odj["coordinates"]

            latitude_drone = lat_current
            longitude_drone = lon_current
            direction_drone = 80  # направление дрона

            latitude_object, longitude_object = calc_coord(h_object, altitude_drone, theta_vertical,
                                                           theta_horizontal, fov_vertical, fov_horizontal, w_image,
                                                           h_image,
                                                           x1, y1, x2, y2, latitude_drone, longitude_drone,
                                                           direction_drone)
            return f"Обнаружен человек в координате: {latitude_object:.4f}, {longitude_object:.4f}"

def spiral_search(drone, client, start_lat, start_lon, end_lat, end_lon, step, altitude):  # полет по спирали
    radius = 0
    angle = 0
    begin_lat = start_lat + (end_lat - start_lat) / 2
    begin_lon = start_lon + (end_lon - start_lon) / 2

    while radius <= (end_lon - start_lon) / 2:
        radius += step
        angle += math.pi / 180
        x = math.sin(angle) * radius
        y = math.cos(angle) * radius
        lat_current = begin_lat + x
        lon_current = begin_lon + y
        # паттерн Flyweight для управления координатами
        coordinate = CoordinateFlyweight.get_coordinate(lat_current, lon_current)
        coordinates.append(coordinate)
        # Запрос изображений с камеры дрона (0 - идентификатор камеры)
        responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
        message_human = object_detection("r", lat_current, lon_current)
        if message_human:
            yield message_human
        yield message_human
        drone.global_position_control(lat=lat_current, lon=lon_current, alt=altitude)
        time.sleep(5)
    yield coordinate
    # Возврат на исходную точку
    drone.global_position_control(lat=start_lat, lon=start_lon, alt=altitude)
    time.sleep(1)


def main_begin(client, api):          # основной метод
    client.confirmConnection()

    client.enableApiControl(True)
    client.armDisarm(True)

def main_end(client, api):            # окончание полета
    client.takeoffAsync().join()
    asyncio.gather(
        api.get_telemetry(client)
    )
    client.armDisarm(False)
    client.enableApiControl(False)


if __name__ == '__main__':
    app.run(debug=True)