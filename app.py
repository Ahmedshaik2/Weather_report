from flask import Flask, render_template, request, redirect, url_for, session
import requests
from flask_bcrypt import Bcrypt
import pymysql

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
#MySQL config
connection = pymysql.connect(
    host='localhost', 
    database='weather_app',
    user='root', 
    password='1234567890', 
    )
cursor = connection.cursor()
#Creating a Table
mySql_Create_Table_Query = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);
"""
cursor.execute( mySql_Create_Table_Query)
connection.commit()

create_weather_table_query = """
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    location VARCHAR(255),
    description VARCHAR(255),
    temperature FLOAT,
    humidity FLOAT,
    feels_like FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""
cursor.execute(create_weather_table_query)
connection.commit()

def get_weather_data(location):
    api_key = 'b7cd20a092c95c520c525b859263c03b'
    url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}'
    response = requests.get(url)
    data = response.json()

    try:
        main_data = data.get('current')
        if main_data:
            condition_data = main_data.get('condition')
            if condition_data:
                description = condition_data.get('text')
                temperature = main_data.get('temp')('temp_c')
                humidity = main_data.get('humidity')
                feels_like = main_data.get('feelslike_c')

                return {
                    'description': description,
                    'temperature': temperature,
                    'humidity': humidity,
                    'feels_like': feels_like,
                }

    except KeyError as e:
        print(f"KeyError in get_weather_data: {e}")
    except Exception as e:
        print(f"Exception in get_weather_data: {e}")
    print(f"Faile to fetch weather data for location:{location}")
    return {
        'description': 'N/A',
        'temperature': 'N/A',
        'humidity': 'N/A',
        'feels_like': 'N/A',
    }
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        select_user_query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(select_user_query, (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid User ID or Password')

    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        select_user_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(select_user_query, (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', error='Username already Registered')
        insert_user_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(insert_user_query, (username, password))
        connection.commit()

        return redirect(url_for('login'))

    return render_template('register.html', error=None)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        location = request.form['location']
        weather_data = get_weather_data(location)

        if weather_data:
            insert_query = """
                INSERT INTO weather_data (user_id, location, description, temperature, humidity, feels_like)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

            try:
                 
                if weather_data['temperature'] != 'N/A':
                    temperature = float(weather_data['main']['temperature'] - 127.5)
                else:
                    temperature = None
                
                if weather_data['humidity'] != 'N/A':
                    humidity = float(weather_data['main']['humidity']) 

                else:
                    humidity = None
                 
                if weather_data['feels_like'] != 'N/A':
                    feels_like = float(weather_data['main']['feels_like'])
                else:
                    feels_like = None
                cursor.execute(insert_query, (
                session['user_id'],
                location,
                weather_data['description'],
                temperature,
                humidity,
                feels_like
                ))
                connection.commit()
            except ValueError as ve:
                print(f"Error converting temperature to float: {ve}")
                connection.rollback()
            except Exception as e:
                print(f"Error executing SQL query: {e}")
            connection.rollback()
    select_query = "SELECT * FROM weather_data WHERE user_id = %s ORDER BY id DESC LIMIT 1"
    cursor.execute(select_query, (session['user_id'],))
    result = cursor.fetchone()

    return render_template('dashboard.html', weather_data=result)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
