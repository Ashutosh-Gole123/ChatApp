from flask_socketio import emit, join_room
from datetime import datetime
from ai_services import AIService
from flask import request
import mysql.connector
from API import All_Users
# Establish MySQL connection (reuse your original configuration)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ashu@123",
    database="ChatApp"
)
cursor = db.cursor(dictionary=True)

chat_rooms = {}
message_history = {}

def register_socket_handlers(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"[Socket] User connected: {request.sid}")
        emit('connected', {'status': 'Connected to server'})

    @socketio.on('join_room')
    def handle_join_room(data):
        chat_id = data.get('chat_id')
        join_room(chat_id)
        chat_rooms.setdefault(chat_id, [])
        message_history.setdefault(chat_id, [])
        emit('room_joined', {'chat_id': chat_id})

    @socketio.on('send_message')
    def handle_send_message(data):
        chat_id = data['chat_id']
        sentiment = AIService.analyze_sentiment(data['message'])
        data['sentiment'] = sentiment

        # Save message to MySQL
        cursor.execute("INSERT INTO ChatMessages (chat_id, sender_id, receiver_id, message, timestamp) VALUES (%s, %s, %s, %s, %s)",
                       (chat_id, data['sender_email'], data['receiver_email'], data['message'], datetime.now()))
        db.commit()

        emit('new_message', data, room=chat_id)

    @socketio.on('fetch_messages')
    def handle_fetch_messages(data):
        chat_id = data.get('chat_id')
        cursor.execute("SELECT * FROM ChatMessages WHERE chat_id = %s", (chat_id,))
        messages = cursor.fetchall()
        emit('messages_fetched', {'messages': messages})

    @socketio.on('get_smart_replies')
    def handle_smart_replies(data):
        chat_id = data['chat_id']
        replies = AIService.smart_reply_suggestions(message_history.get(chat_id, []))
        emit('smart_replies_generated', {'suggestions': replies})

    @socketio.on('translate_message')
    def handle_translate_message(data):
        translated = AIService.translate_message(data['text'], data.get('target_language', 'es'))
        emit('message_translated', {'original': data['text'], 'translated': translated})

    @socketio.on('enhance_message')
    def handle_enhance_message(data):
        enhanced = AIService.enhance_message(data['text'], data.get('type', 'grammar'))
        emit('message_enhanced', {'original': data['text'], 'enhanced': enhanced})

    @socketio.on('summarize_conversation')
    def handle_summarize_conversation(data):
        chat_id = data['chat_id']
        summary = AIService.summarize_conversation(message_history.get(chat_id, []))
        emit('conversation_summarized', {'summary': summary})

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"[Socket] Disconnected: {request.sid}")