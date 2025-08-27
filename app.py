from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")  # fallback in case .env missing

# MongoDB setup (URI comes from .env file)
client = MongoClient(os.getenv("MONGO_URI"))
db = client['leftover_db']
users = db['users']
posts = db['posts']


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = {
            'name': request.form['name'],
            'quantity': request.form['quantity'],
            'location': request.form['location'],
            'phone': request.form['phone'],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        posts.insert_one(data)
        return redirect('/')

    search = request.args.get('search', '')
    query = {"$or": [
        {"location": {"$regex": search, "$options": "i"}},
        {"name": {"$regex": search, "$options": "i"}}
    ]} if search else {}

    data = posts.find(query).sort("timestamp", -1)
    return render_template('index.html', posts=data)


@app.route('/delete/<post_id>')
def delete_post(post_id):
    if 'username' in session:
        posts.delete_one({'_id': ObjectId(post_id)})
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({'username': request.form['username']})
        if user and user['password'] == request.form['password']:
            session['username'] = user['username']
            return redirect('/')
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if users.find_one({'username': request.form['username']}):
            return render_template('register.html', error='Username already exists')
        users.insert_one({
            'username': request.form['username'],
            'password': request.form['password']
        })
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True, port=5006)
