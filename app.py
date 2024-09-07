import math
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import requests
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
        real_drone = AirSimAPI()
        drone = DJIDroneProxy(real_drone)
        #drone.connect()
        #time.sleep(2)
        drone.takeoff()
        time.sleep(4)
        data = spiral_search(drone, start_lat=data_from_drones["start_lat"], start_lon=data_from_drones["start_lon"],
                  end_lat=data_from_drones["end_lat"], end_lon=data_from_drones["end_lon"],
                  step=data_from_drones["step"], altitude=data_from_drones["altitude"])
        # message_human = object_detection("jpg/man_in_forest2.jpg")
        #human= [{"message": message_human}]
        return render_template('message_human.html', data=data)

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

def object_detection(photo):
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

            latitude_drone = 37.662941
            longitude_drone = 55.732247
            direction_drone = 80  # направление дрона

            latitude_object, longitude_object = calc_coord(h_object, altitude_drone, theta_vertical,
                                                           theta_horizontal, fov_vertical, fov_horizontal, w_image,
                                                           h_image,
                                                           x1, y1, x2, y2, latitude_drone, longitude_drone,
                                                           direction_drone)
            return f"Обнаружен человек в координате: {latitude_object:.4f}, {longitude_object:.4f}"

def spiral_search(drone, start_lat, start_lon, end_lat, end_lon, step, altitude):
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
        # Используем паттерн Flyweight для управления координатами
        coordinate = CoordinateFlyweight.get_coordinate(lat_current, lon_current)
        coordinates.append(coordinate)
        yield coordinate
        # Управляем дроном через прокси
        drone.global_position_control(lat=lat_current, lon=lon_current, alt=altitude)
        # time.sleep(1)


if __name__ == '__main__':
    app.run(debug=True)