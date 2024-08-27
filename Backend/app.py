from flask import Flask, request, jsonify
from mysql.connector import Error
from flask_cors import CORS
from Auth import register_user, login_user

app = Flask(__name__)
CORS(app)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Track users
users = []




# @socketio.on('connect')
# def on_connect():
#     print("A user connected")

# @socketio.on('add_user')
# def add_user(data):
#     username = data['username']
#     if username not in users:
#         users.append(username)
#     emit('update_user_list', users, broadcast=True)

# @socketio.on('create_room')
# def create_room(data):
#     room = data['room']
#     username = data['username']
#     join_room(room)
#     send(f"{username} has entered the room.", to=room)
#     emit('message', f"{username} has entered the room.", room=room)

# @socketio.on('leave_room')
# def leave_room_event(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     send(f"{username} has left the room.", to=room)
#     emit('message', f"{username} has left the room.", room=room)

# @socketio.on('message')
# def handle_message(data):
#     room = data['room']
#     message = data['message']
#     send(message, to=room)  # This sends the message to all clients in the room

@app.route('/register', methods=['POST'])
def register():
    data = request.form  # Assuming form data
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    profile_image = request.files.get('image')
    
    # Read the image file
    profile_image_data = profile_image.read() if profile_image else None

    response = register_user(username, password, email, profile_image_data)
    return jsonify(response)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('email')
    password = data.get('password')
    
    response = login_user(username, password)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
