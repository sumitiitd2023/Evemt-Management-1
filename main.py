from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory,flash, session
import json
from pymongo import MongoClient
from datetime import datetime
import calendar
from bson import ObjectId
import os
from flask_session import Session
from functools import wraps  # Added this import

# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super(JSONEncoder, self).default(o)


app = Flask(__name__)
app.json_encoder = JSONEncoder

# MongoDB connection
client = MongoClient('mongodb://root:cda123@localhost:27017/')
db = client['event_calendar']
events_collection = db['events']

# Directory for file uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.secret_key = 'your_secret_key_here'  # Replace with a secure key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dummy user data (replace with database in production)
users = {
    'admin': 'password123'
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists. Please choose another.', 'danger')
        else:
            users[username] = password  # In production, hash the password
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


# @app.route('/')
# def index():
#     return render_template('index.html')


@app.route('/base')
@login_required
def base():
    return render_template('base.html')

@app.route('/event_form')
@login_required
def event_form():
    date = request.args.get('date')
    existing_events = list(events_collection.find({'date': date}))
    return render_template('event_form.html', date=date, existing_events=existing_events)


@app.route('/view_event/<event_id>')
@login_required
def view_event(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if event:
        return render_template('view_event.html', event=event)
    return redirect(url_for('index'))


@app.route('/get_events', methods=['GET'])
@login_required
def get_events():
    month = int(request.args.get('month'))
    year = int(request.args.get('year'))

    start_date = datetime(year, month, 1)
    end_date = start_date.replace(day=calendar.monthrange(year, month)[1])

    events = list(events_collection.find(
        {
            'date': {
                '$gte': start_date.strftime('%Y-%m-%d'),
                '$lte': end_date.strftime('%Y-%m-%d')
            }
        },
        {'_id': 0}  # Exclude _id field
    ))
    print(events)

    return jsonify(events)


@app.route('/save_event', methods=['POST'])
@login_required
def save_event():
    data = request.form
    files = request.files

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    event_title = data['title'].replace(' ', '_')
    folder_name = f"{timestamp}-{event_title}"
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    os.makedirs(upload_path, exist_ok=True)

    responsibilities = data.getlist('responsibilities') if 'responsibilities' in data else []

    event = {
        'title': data['title'],
        'description': data['description'],
        'date': data['date'],
        'responsibilities': responsibilities,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'folder': folder_name,
        'files': []
    }

    for file_type in ['aip', 'quotation', 'bill', 'other']:
        if file_type in files and files[file_type].filename:
            file = files[file_type]
            filename = file.filename
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            relative_path = os.path.join(folder_name, filename)
            event['files'].append({
                'type': file_type,
                'filename': filename,
                'path': relative_path
            })

    events_collection.insert_one(event)
    return redirect(url_for('index'))


@app.route('/update_event/<event_id>', methods=['POST'])
@login_required
def update_event(event_id):
    data = request.form
    files = request.files

    existing_event = events_collection.find_one({'_id': ObjectId(event_id)})
    folder_name = existing_event['folder']
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    responsibilities = data.getlist('responsibilities') if 'responsibilities' in data else []

    updated_event = {
        'title': data['title'],
        'description': data['description'],
        'date': data['date'],
        'responsibilities': responsibilities,
        'created_at': data['created_at'],
        'folder': folder_name,
        'files': existing_event['files']
    }

    for file_type in ['aip', 'quotation', 'bill', 'other']:
        if file_type in files and files[file_type].filename:
            file = files[file_type]
            filename = file.filename
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            relative_path = os.path.join(folder_name, filename)
            updated_event['files'] = [f for f in updated_event['files'] if f['type'] != file_type]
            updated_event['files'].append({
                'type': file_type,
                'filename': filename,
                'path': relative_path
            })

    events_collection.update_one({'_id': ObjectId(event_id)}, {'$set': updated_event})
    return redirect(url_for('index'))


@app.route('/delete_event/<event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = events_collection.find_one({'_id': ObjectId(event_id)})
    if event and 'folder' in event:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], event['folder'])
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
    events_collection.delete_one({'_id': ObjectId(event_id)})
    return redirect(url_for('index'))


@app.route('/uploads/<path:filename>')
@login_required
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')