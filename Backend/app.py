from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Track users
users = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('add_user')
def add_user(data):
    username = data['username']
    if username not in users:
        users.append(username)
    emit('update_user_list', users, broadcast=True)

@socketio.on('create_room')
def create_room(data):
    room = data['room']
    username = data['username']
    join_room(room)
    send(f"{username} has entered the room.", to=room)
    emit('message', f"{username} has entered the room.", room=room)

@socketio.on('leave_room')
def leave_room_event(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(f"{username} has left the room.", to=room)
    emit('message', f"{username} has left the room.", room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    send(message, to=room)  # This sends the message to all clients in the room

if __name__ == '__main__':
    socketio.run(app, debug=True)
