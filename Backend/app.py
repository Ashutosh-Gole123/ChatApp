import uuid  # Import the uuid module
from flask import Flask, request, jsonify, Blueprint, send_file
from flask_socketio import SocketIO,emit,join_room
from mysql.connector import Error
from flask_cors import CORS
from Auth import register_user, login_user, connection
from API import All_Users
import logging  # Import logging for error tracking
import mysql.connector
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import base64

# Add to the top of your file
user_socket_map = {}  # email -> socket.id

# Blueprint (optional, otherwise just use @app.route)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Configure CORS for Flask
CORS(app) 
# Configure Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")


@app.route('/register', methods=['POST'])
def register():
    try:
        print("Register request received.")

        # Access form fields
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        profile_image = request.files.get('profile_image')  # Optional

        print(f"Received data: username={username}, email={email}")

        if not username or not email or not password:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        image_data = profile_image.read() if profile_image else None

        result = register_user(username, password, email, image_data)

        if result.get("status") == "User registered successfully":
            return jsonify({'status': 'success', 'message': result['status']}), 200
        else:
            return jsonify({'status': 'error', 'message': result['status']}), 500


    except Exception as e:
        print(f"Exception in /register: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400

        username = data.get('email')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400

        response = login_user(username, password)  # Your custom function
        return jsonify(response), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500


# ----- API to fetch users -----
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = All_Users()  # Your custom function that fetches user data
        return jsonify({'status': 'success', 'users': users}), 200

    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch users'}), 500

# Handle socket connection
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected to server'})

def get_db_connection():
    """Function to get a connection to the MySQL database."""
    return connection


@socketio.on('register_user')
def handle_register_user(data):
    email = data.get('email')
    if email:
        user_socket_map[email] = request.sid
        print(f"{email} registered with socket {request.sid}")

@socketio.on('add_contact_notification')
def handle_add_contact_notification(data):
    user_email = data.get('userEmail')
    contact_email = data.get('contactEmail')
    contact_sid = user_socket_map.get(contact_email)
    if contact_sid:
        emit('new_contact_added', {'userEmail': user_email, 'contactEmail': contact_email}, to=contact_sid)

@socketio.on('remove_contact_notification')
def handle_remove_contact_notification(data):
    user_email = data.get('userEmail')
    contact_email = data.get('contactEmail')
    contact_sid = user_socket_map.get(contact_email)
    if contact_sid:
        emit('contact_removed', {'userEmail': user_email, 'contactEmail': contact_email}, to=contact_sid)


@socketio.on('create_chat_session')
def handle_create_chat_session(data):
    email1 = data['user1']  # Sender's email
    email2 = data['user2']  # Receiver's email

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
        # Join the room corresponding to the chat session
        join_room(chat_id)

        # Emit the chat session ID to the client
        emit('chat_session_created', {'chat_id': chat_id})

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'A database error occurred. Please try again.'})
        return

    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred. Please try again.'})
        return

    # Emit the chat session ID to the client
    emit('chat_session_created', {'chat_id': chat_id})

@socketio.on('join_room')
def handle_join_room(data):
    chat_id = data.get('chat_id')
    print(chat_id)
    if not chat_id:
        emit('error', {'message': 'Chat ID is required to join a room.'})
        return

    # Join the specified room
    join_room(chat_id)
    emit('room_joined', {'chat_id': chat_id})
    logging.info(f"User has joined room: {chat_id}")


@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data.get('chat_id')
    sender_email = data.get('sender_email')
    receiver_email = data.get('receiver_email')
    message = data.get('message')
    image = data.get('image')  # Optional image data

    if not chat_id or not sender_email or not receiver_email or not message:
        emit('error', {'message': 'Chat ID, sender ID, and message are required.'})
        return


    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate a UUID for the message
        message_id = str(uuid.uuid4())
        cursor.execute("""
        SELECT user_id FROM Users WHERE email = %s
        """, (sender_email,))
        sender_ids = cursor.fetchone()
        sender_id = sender_ids[0]

        cursor.execute("""
        SELECT user_id FROM Users WHERE email = %s
        """, (receiver_email,))
        receiver_ids = cursor.fetchone()

        receiver_id = receiver_ids[0]

        # Insert the message into the ChatMessage table
        cursor.execute("""
        INSERT INTO ChatMessage (message_id, chat_id, sender_id, receiver_id, message) VALUES (%s, %s, %s, %s, %s)
        """, (message_id, chat_id, sender_id, receiver_id, message))
        conn.commit()

        # Optionally handle image data
        if image:
            cursor.execute("""
            INSERT INTO ChatMessageImages (message_id, chat_id, sender_id, file_name, file_type, file_url) VALUES (%s, %s, %s, %s, %s, %s)
            """, (message_id, chat_id, sender_id, image['file_name'], image['file_type'], image['file_data']))  # Adjust storage as needed
            conn.commit()
        # Example logging
        logging.info("Emitting new message: %s", {
            'message_id': message_id,
            'chat_id': chat_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        emit('new_message', {
            'message_id': message_id,
            'chat_id': chat_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, room=chat_id)

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'An error occurred while sending the message.'})
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred. Please try again.'})

@socketio.on('fetch_messages')
def handle_fetch_messages(data):
    chat_id = data.get('chat_id')

    if not chat_id:
        emit('error', {'message': 'Chat ID is required.'})
        return

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch messages for the specified chat_id
        cursor.execute("""
        SELECT message_id, sender_id, receiver_id, message, timestamp 
        FROM ChatMessage WHERE chat_id = %s ORDER BY timestamp ASC
        """, (chat_id,))

        messages = cursor.fetchall()


# Format datetime objects in each message
        for message in messages:
            if isinstance(message['timestamp'], datetime):
                message['timestamp'] = message['timestamp'].isoformat()

        emit('messages_fetched', {'messages': messages})
        

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'An error occurred while fetching messages.'})
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred.'})
    # finally:
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()


@socketio.on('disconnect')
def handle_disconnect():
    disconnected_sid = request.sid
    email_to_remove = None
    for email, sid in user_socket_map.items():
        if sid == disconnected_sid:
            email_to_remove = email
            break
    if email_to_remove:
        del user_socket_map[email_to_remove]
        print(f"{email_to_remove} disconnected from socket {disconnected_sid}")


@app.route('/user/profile', methods=['GET'])
def get_profile():
    email = request.args.get('email')

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    cursor = connection.cursor()
    # Add timestamp to query to prevent caching
    current_time = datetime.now().timestamp()
    
    cursor.execute("SELECT username, email, profile_image FROM Users WHERE email = %s", (email,))
    result = cursor.fetchone()

    if not result:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    username, email, profile_image = result

    # If the image is stored as binary, encode it to base64
    image_url = None
    if profile_image:
        try:
            # Create a proper data URL format
            base64_image = base64.b64encode(profile_image).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{base64_image}"
            # Don't append cache-busting parameters to data URLs
        except Exception as e:
            logging.error(f"Error encoding profile image: {e}")
            # If encoding fails, return null instead of crashing
            image_url = None

    return jsonify({
        'name': username,
        'email': email,
        'image': image_url,
        'timestamp': current_time  # Include timestamp in response
    })

@app.route('/user/profile', methods=['PUT'])
def update_profile():
    data = request.form
    image = request.files.get('image')
    email = data.get('email')  # Get email from form data
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Using mysql.connector connection and cursor
    cursor = connection.cursor()

    # Build update query dynamically
    update_fields = []
    update_values = []

    if 'name' in data:
        update_fields.append("username = %s")
        update_values.append(data['name'])

    if 'email' in data:
        # If user is changing email, make sure it's not already taken
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (data['email'],))
        existing = cursor.fetchone()
        if existing:
            current_email = email  # Current email
            if data['email'] != current_email:
                return jsonify({"error": "Email already taken"}), 400
        
        update_fields.append("email = %s")
        update_values.append(data['email'])

    if image:
        image_data = image.read()
        update_fields.append("profile_image = %s")
        update_values.append(image_data)

    if not update_fields:
        return jsonify({"message": "No data provided for update"}), 400

    # Get the user_id from email
    cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
    user_result = cursor.fetchone()
    
    if not user_result:
        return jsonify({"error": "User not found"}), 404
        
    user_id = user_result[0]
    update_values.append(user_id)  # For WHERE clause

    sql_update = f"UPDATE Users SET {', '.join(update_fields)} WHERE user_id = %s"

    try:
        cursor.execute(sql_update, update_values)
        connection.commit()
        
        # Update the email in localStorage if it was changed
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

@app.route('/api/last-messages/<email>', methods=['GET'])
def get_last_messages(email):
    try:
        cursor = connection.cursor(dictionary=True)

        # Get current user ID
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        user_id = user['user_id']

        # Get latest message with each contact
        cursor.execute("""
            SELECT 
                cm.chat_id,
                cm.message,
                cm.timestamp,
                u.username,
                u.email,
                u.profile_image,
                cm.sender_id,
                cm.receiver_id
            FROM ChatMessage cm
            JOIN (
                SELECT chat_id, MAX(timestamp) as max_time
                FROM ChatMessage
                GROUP BY chat_id
            ) latest ON cm.chat_id = latest.chat_id AND cm.timestamp = latest.max_time
            JOIN ChatSession cs ON cs.chat_id = cm.chat_id
            JOIN Users u ON (u.user_id = cs.user1_id OR u.user_id = cs.user2_id)
            WHERE (cs.user1_id = %s OR cs.user2_id = %s)
              AND u.user_id != %s
        """, (user_id, user_id, user_id))

        messages = cursor.fetchall()

        for msg in messages:
            if msg['profile_image']:
                msg['profile_image'] = base64.b64encode(msg['profile_image']).decode('utf-8')
            msg['timestamp'] = msg['timestamp'].isoformat()

        return jsonify({'status': 'success', 'messages': messages})

    except Exception as e:
        logging.error(f"Error in get_last_messages: {e}")
        return jsonify({'status': 'error', 'message': 'Internal error'}), 500


# Get a user's contacts
@app.route('/api/contacts/<email>', methods=['GET'])
def get_contacts(email):
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user ID from email
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        user_id = user_result['user_id']
        
        # Get all contacts for this user
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, u.profile_image 
            FROM Contacts c
            JOIN Users u ON c.contact_user_id = u.user_id
            WHERE c.user_id = %s
        """, (user_id,))
        
        contacts = cursor.fetchall()
        
        # Process the results
        processed_contacts = []
        for contact in contacts:
            # Convert binary profile image to base64 string if it exists
            profile_image = None
            if contact['profile_image']:
                import base64
                profile_image = base64.b64encode(contact['profile_image']).decode('utf-8')
                
            processed_contacts.append({
                'user_id': contact['user_id'],
                'username': contact['username'],
                'email': contact['email'],
                'profile_image': profile_image
            })
            
        return jsonify({'status': 'success', 'contacts': processed_contacts}), 200
        
    except mysql.connector.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500
    finally:
        cursor.close()

# Add a new contact
@app.route('/api/contacts', methods=['POST'])
def add_contact():
    data = request.get_json()
    
    user_email = data.get('userEmail')
    contact_email = data.get('contactEmail')
    
    if not user_email or not contact_email:
        return jsonify({'status': 'error', 'message': 'Both user and contact emails are required'}), 400
        
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user IDs from emails
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return jsonify({'status': 'error', 'message': 'One or both users not found'}), 404
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Check if the contact already exists
        cursor.execute("""
            SELECT contact_id FROM Contacts
            WHERE user_id = %s AND contact_user_id = %s
        """, (user_id, contact_user_id))
        
        if cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Contact already exists'}), 409
            
        # Create contact in both directions for bidirectional relationship
        contact_id1 = str(uuid.uuid4())
        contact_id2 = str(uuid.uuid4())
        
        # Add first direction
        cursor.execute("""
            INSERT INTO Contacts (contact_id, user_id, contact_user_id)
            VALUES (%s, %s, %s)
        """, (contact_id1, user_id, contact_user_id))
        
        # Add second direction
        cursor.execute("""
            INSERT INTO Contacts (contact_id, user_id, contact_user_id)
            VALUES (%s, %s, %s)
        """, (contact_id2, contact_user_id, user_id))
        
        connection.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contact added successfully'
        }), 201
        
    except mysql.connector.Error as e:
        connection.rollback()
        logging.error(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Database error occurred'}), 500
    except Exception as e:
        connection.rollback()
        logging.error(f"Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500
    finally:
        cursor.close()

# Remove a contact
@app.route('/api/contacts', methods=['DELETE'])
def remove_contact():
    data = request.get_json()
    
    user_email = data.get('userEmail')
    contact_email = data.get('contactEmail')
    
    if not user_email or not contact_email:
        return jsonify({'status': 'error', 'message': 'Both user and contact emails are required'}), 400
        
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user IDs from emails
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return jsonify({'status': 'error', 'message': 'One or both users not found'}), 404
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Remove contact in both directions
        cursor.execute("""
            DELETE FROM Contacts
            WHERE (user_id = %s AND contact_user_id = %s)
            OR (user_id = %s AND contact_user_id = %s)
        """, (user_id, contact_user_id, contact_user_id, user_id))
        
        connection.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contact removed successfully'
        }), 200
        
    except mysql.connector.Error as e:
        connection.rollback()
        logging.error(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Database error occurred'}), 500
    except Exception as e:
        connection.rollback()
        logging.error(f"Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred'}), 500
    finally:
        cursor.close()

if __name__ == '__main__':
    socketio.run(app,debug=True)
