from flask import Flask, request, render_template, redirect, url_for, session
from flask_mysqldb import MySQL
import numpy as np
import pickle
import sklearn

print(sklearn.__version__)

dtr = pickle.load(open('dtr.pkl', 'rb'))
preprocessor = pickle.load(open('preprocessor.pkl', 'rb'))

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user'
app.config['MYSQL_PASSWORD'] = 'user'
app.config['MYSQL_DB'] = 'crop_yield_db'

mysql = MySQL(app)

@app.route('/')
def index():
  if 'loggedin' in session:
    return redirect(url_for('dashboard'))
  return render_template('index.html')

@app.route("/predict", methods=['POST', 'GET'])
def predict():
  if request.method == 'POST':
    Year = request.form['Year']
    average_rain_fall_mm_per_year = request.form['average_rain_fall_mm_per_year']
    pesticides_tonnes = request.form['pesticides_tonnes']
    avg_temp = request.form['avg_temp']
    Area = request.form['Area']
    Item = request.form['Item']

    features = np.array([[Year, average_rain_fall_mm_per_year, pesticides_tonnes, avg_temp, Area, Item]], dtype=object)
    
    transformed_features = preprocessor.transform(features)
    
    prediction = dtr.predict(transformed_features).reshape(1, -1)

    return render_template('dashboard.html', prediction=prediction[0][0])

  return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
  if 'loggedin' in session:
    return redirect(url_for('dashboard'))
  
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    account = cursor.fetchone()
    
    if account and account[2] == password:
      session['loggedin'] = True
      session['id'] = account[0]
      session['username'] = account[1]
      return redirect(url_for('dashboard'))
    else:
      return "Incorrect username or password!"

  return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
  if 'loggedin' in session:
    return redirect(url_for('dashboard'))
  
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
      return "Username already exists!"
    
    cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('login'))

  return render_template('register.html')

@app.route('/dashboard')
def dashboard():
  if 'loggedin' in session:
    return render_template('dashboard.html', username=session['username'])
  return redirect(url_for('login'))

@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('index'))

if __name__ == '__main__':
  app.run(port=3000, debug=True)