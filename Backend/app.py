import uuid  # Import the uuid module
from flask import Flask, request, jsonify
from flask_socketio import SocketIO,emit
from mysql.connector import Error
from flask_cors import CORS
from Auth import register_user, login_user, connection
from API import All_Users
import logging  # Import logging for error tracking
import mysql.connector
# Configure logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)






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


# Registration route
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

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('email')
    password = data.get('password')   
    response = login_user(username, password)
    return jsonify(response)

# API endpoint to fetch users data
@app.route('/api/users', methods=['GET'])
def get_users():
    """API endpoint to fetch all users and send to the frontend."""
    users = All_Users()
    return jsonify(users)

# Handle socket connection
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected to server'})

def get_db_connection():
    """Function to get a connection to the MySQL database."""
    return connection

@socketio.on('create_chat_session')
def handle_create_chat_session(data):
    email1 = data['user1']  # Sender's email
    email2 = data['user2']  # Receiver's email

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get user IDs corresponding to the email addresses
        cursor.execute("""
        SELECT user_id FROM Users WHERE email = %s
        """, (email1,))
        user1 = cursor.fetchone()

        cursor.execute("""
        SELECT user_id FROM Users WHERE email = %s
        """, (email2,))
        user2 = cursor.fetchone()

        # Ensure both users exist
        if not user1 or not user2:
            emit('error', {'message': 'One or both users do not exist.'})
            return

        user1_id = user1[0]
        user2_id = user2[0]

        # Check if a chat session already exists between these two users
        cursor.execute("""
        SELECT chat_id FROM ChatSession WHERE 
        (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
        """, (user1_id, user2_id, user2_id, user1_id))
        result = cursor.fetchone()

        if result:
            # Chat session already exists
            chat_id = result[0]
        else:
            # No existing chat session found; create a new one with a UUID
            chat_id = str(uuid.uuid4())  # Generate a new UUID
            cursor.execute("""
            INSERT INTO ChatSession (chat_id, user1_id, user2_id) VALUES (%s, %s, %s)
            """, (chat_id, user1_id, user2_id))
            conn.commit()

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'A database error occurred. Please try again.'})
        return

    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred. Please try again.'})
        return

    # finally:
    #     # Ensure the cursor and connection are always closed properly
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()

    # Emit the chat session ID to the client
    emit('chat_session_created', {'chat_id': chat_id})

@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data.get('chat_id')
    email = data.get('sender_id')
    message = data.get('message')
    image = data.get('image')  # Optional image data

    if not chat_id or not email or not message:
        emit('error', {'message': 'Chat ID, sender ID, and message are required.'})
        return

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate a UUID for the message
        message_id = str(uuid.uuid4())
        cursor.execute("""
        SELECT user_id FROM Users WHERE email = %s
        """, (email,))
        sender_ids = cursor.fetchone()

        sender_id = sender_ids[0]

        # Insert the message into the ChatMessage table
        cursor.execute("""
        INSERT INTO ChatMessage (message_id, chat_id, sender_id, message) VALUES (%s, %s, %s, %s)
        """, (message_id, chat_id, sender_id, message))
        conn.commit()

        # Optionally handle image data
        if image:
            cursor.execute("""
            INSERT INTO ChatMessageImages (message_id, chat_id, sender_id, file_name, file_type, file_url) VALUES (%s, %s, %s, %s, %s, %s)
            """, (message_id, chat_id, sender_id, image['file_name'], image['file_type'], image['file_data']))  # Adjust storage as needed
            conn.commit()

        emit('new_message', data, room=chat_id)

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'An error occurred while sending the message.'})
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred. Please try again.'})
    # finally:
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app,debug=True)
