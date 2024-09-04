from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)

app = Flask(__name__)
authorization = False

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

def security(func):
    def wrapper(*args, **kwargs):
        global authorization
        if authorization:
            func(*args, **kwargs)
    return wrapper()

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
    return render_template('index.html')     # возвращает из папки template файл index.html

@app.route('/<int:drone_id>')   # в индексе целое число
def get_drone(drone_id):         # получает данные по drone_id
    connect = get_db_connection()
    # запрашивается из базы данных по айдишнику и берется одна строка функцией fetchone()
    drone = connect.execute('SELECT * FROM drones WHERE id = ?', (drone_id,)).fetchone()
    connect.close()
    # рендерит HTML-шаблон и передает туда полученный пост
    return render_template('post.html', drone=drone)

@app.route('/new_user', methods=['GET', 'POST'])
def new_post():
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
def new_drone():
    if request.method == 'POST':
        model = request.form['model']
        manufactured = request.form['manufactured']

        conn = get_db_connection()
        conn.execute('INSERT INTO drones (model, manufactured) VALUES (?, ?)', (model, manufactured))
        conn.commit()
        conn.close()
        return redirect(url_for('main_window'))
    return render_template('add_drone.html')

@app.route('/main_window', methods=['GET', 'POST'])
def main_window():
    return render_template('main.html')

with app.app_context():  # перед первым запросов к базе данных
    init_db()            # Инициализировать базу данных

if __name__ == '__main__':
    app.run(debug=True)