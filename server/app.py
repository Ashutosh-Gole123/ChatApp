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
import requests
import json
import re
from transformers import pipeline
import torch
from huggingface_hub import login
from transformers import AutoModelForCausalLM, AutoTokenizer

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

# Hugging Face API configuration
HF_API_KEY = os.getenv("HF_API_KEY")  # Get this from huggingface.co/settings/tokens
HF_API_URL = "https://api-inference.huggingface.co/models/"
login(HF_API_KEY)

# Initialize local models for faster processing (optional)
try:
    # Load lightweight models locally for better performance
    sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except Exception as e:
    print(f"Could not load local models: {e}")
    sentiment_analyzer = None
    summarizer = None

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
class AIService:
    @staticmethod  
    def call_huggingface_api(model_name, payload):
        """Enhanced API call with better error handling"""
        HF_API_URL = "https://api-inference.huggingface.co/models"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}

        try:
            print(f"Making API call to: {HF_API_URL}/{model_name}")
            response = requests.post(
                f"{HF_API_URL}/{model_name}", 
                headers=headers, 
                json=payload, 
                timeout=30
            )

            print(f"API Response Status: {response.status_code}")
            print(f"API Response Text: {response.text}")

            if response.status_code == 503:
                # Model is loading, wait and retry
                print("Model is loading, waiting 10 seconds...")
                import time
                time.sleep(10)
                response = requests.post(
                    f"{HF_API_URL}/{model_name}", 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                )

            if response.status_code != 200:
                logging.error(f"Hugging Face API returned {response.status_code}: {response.text}")
                return None

            result = response.json()
            print(f"API Response JSON: {result}")
            return result
            
        except requests.exceptions.Timeout:
            logging.error("Hugging Face API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to call Hugging Face API: {e}")
            return None

    
    @staticmethod
    def smart_reply_suggestions(message_history, num_replies=3):
        try:
            if not message_history:
                return ["Hello!", "How are you?", "That's great!"]

            # Ensure we extract 'message' field from each dictionary safely
            context = " ".join([msg.get("message", "") for msg in message_history[-3:]]).strip()

            if not context:
                return ["Okay!", "Sure!", "Alright!"]

            # Encode context
            input_ids = tokenizer.encode(context + tokenizer.eos_token, return_tensors="pt")

            # Generate multiple reply candidates
            outputs = model.generate(
                input_ids,
                max_length=100,
                pad_token_id=tokenizer.eos_token_id,
                num_return_sequences=num_replies,
                num_beams=num_replies,
                do_sample=True,
                top_k=50,
                top_p=0.95
            )

            # Decode responses and remove prompt echo or gibberish
            responses = []
            for output in outputs:
                decoded = tokenizer.decode(output, skip_special_tokens=True).strip()
                if decoded and decoded.lower() != context.lower():
                    responses.append(decoded)

            # Filter out bad replies
            filtered = [r for r in responses if len(r) > 5 and r.isascii() and any(c.isalpha() for c in r)]
            return filtered[:num_replies] if filtered else ["Got it.", "Understood.", "Okay!"]

        except Exception as e:
            logging.error(f"Error generating smart replies: {e}")
            return ["Okay.", "Sure.", "Got it."]


    @staticmethod
    def translate_message(text, target_language="es"):
        try:
            models = {
                "es": "Helsinki-NLP/opus-mt-en-es",
                "fr": "Helsinki-NLP/opus-mt-en-fr",
                "de": "Helsinki-NLP/opus-mt-en-de"
            }

            model_name = models.get(target_language)
            if not model_name:
                logging.warning(f"No model found for target language: {target_language}")
                return text

            payload = {
                "inputs": text,
                "options": {"wait_for_model": True}
            }

            response = AIService.call_huggingface_api(model_name, payload)

            # ✅ Add None check before accessing response[0]
            if not response or not isinstance(response, list):
                logging.warning(f"Invalid or empty response from HF API: {response}")
                return text

            translated = response[0].get("translation_text") or response[0].get("generated_text")
            return translated.strip() if translated else text

        except Exception as e:
            logging.error(f"Error translating message: {e}")
            return text

    
    @staticmethod
    def analyze_sentiment(text):
        """Analyze sentiment of message"""
        try:
            if sentiment_analyzer:
                # Use local model
                result = sentiment_analyzer(text)[0]
                return {
                    "sentiment": result['label'].lower().replace('label_', ''),
                    "confidence": result['score']
                }
            else:
                # Use Hugging Face API
                payload = {"inputs": text}
                response = AIService.call_huggingface_api("cardiffnlp/twitter-roberta-base-sentiment-latest", payload)
                
                if response and isinstance(response, list) and len(response) > 0:
                    return {
                        "sentiment": response[0]['label'].lower().replace('label_', ''),
                        "confidence": response[0]['score']
                    }
                return {"sentiment": "neutral", "confidence": 0.5}
                
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    @staticmethod
    def summarize_conversation(messages):
        """Summarize conversation history"""
        try:
            if not messages or len(messages) < 3:
                return "Conversation too short to summarize"
            
            # Combine messages into a single text
            conversation_text = " ".join([f"{msg.get('sender_email', 'User')}: {msg.get('message', '')}" for msg in messages[-20:]])
            
            if len(conversation_text) < 100:
                return "Conversation too short to summarize"
            
            if summarizer and len(conversation_text) < 1024:  # BART has token limits
                # Use local model
                summary = summarizer(conversation_text, max_length=100, min_length=30, do_sample=False)
                return summary[0]['summary_text']
            else:
                # Use a simpler approach for summarization
                payload = {
                    "inputs": f"Summarize this conversation: {conversation_text[:500]}",
                    "parameters": {
                        "max_length": 100,
                        "min_length": 30
                    }
                }
                
                response = AIService.call_huggingface_api("facebook/bart-large-cnn", payload)
                
                if response and isinstance(response, list) and len(response) > 0:
                    if 'summary_text' in response[0]:
                        return response[0]['summary_text']
                
                # Fallback: simple extractive summary
                sentences = conversation_text.split('.')[:3]
                return '. '.join(sentences) + '.'
                
        except Exception as e:
            logging.error(f"Error summarizing conversation: {e}")
            return 'Unable to generate summary'
    
    @staticmethod
    def translate_message(text, target_language):
        """Translate message to target language"""
        print(target_language)
        try:
            # Define model per language
            translation_models = {
                "es": "Helsinki-NLP/opus-mt-en-es",
                "fr": "Helsinki-NLP/opus-mt-en-fr",
                "de": "Helsinki-NLP/opus-mt-en-de",
                "it": "Helsinki-NLP/opus-mt-en-it",
                "pt": "Helsinki-NLP/opus-mt-en-pt"
            }

            model_name = translation_models.get(target_language)
            if not model_name:
                return text  # unsupported

            payload = {
                "inputs": text,
                "options": {"wait_for_model": True}
            }

            response = AIService.call_huggingface_api(model_name, payload)

            if isinstance(response, list) and 'translation_text' in response[0]:
                return response[0]['translation_text'].strip()
            elif 'generated_text' in response[0]:
                return response[0]['generated_text'].strip()

            return text

        except Exception as e:
            logging.error(f"Error translating message: {e}")
            return text

    @staticmethod
    def process_enhancement_response(response, original, prompt=""):
        if isinstance(response, list) and 'generated_text' in response[0]:
            output = response[0]['generated_text'].strip()
            # Remove any prompt echoes if necessary
            return output.replace(prompt, "").strip()
        elif isinstance(response, dict) and 'generated_text' in response:
            return response['generated_text'].strip()
        return original
 
    @staticmethod
    def enhance_message(text, enhancement_type="grammar"):
        try:
            print(f"\n=== ENHANCE MESSAGE DEBUG (Backend) ===")
            print(f"Input text: '{text}'")
            print(f"Enhancement type: '{enhancement_type}'")

            if enhancement_type == "grammar":
                # Simple rule-based grammar fix
                enhanced = text.strip()
                if enhanced and not enhanced[0].isupper():
                    enhanced = enhanced[0].upper() + enhanced[1:]
                if enhanced and enhanced[-1] not in '.!?':
                    enhanced += '.'
                print(f"✅ Grammar enhanced result: '{enhanced}'")
                return enhanced

            # Tone-based enhancement
            elif enhancement_type in ["professional", "casual"]:
                models_to_try = [
                    "pszemraj/flan-t5-large-grammar-synthesis",  # best for grammar+tone
    "Vamsi/T5_Paraphrase_Paws",
    "tuner007/pegasus_paraphrase"                        # Fallback basic model
                ]

                # Construct prompt
                if enhancement_type == "professional":
                    prompt = f"Make this text more professional and formal: {text}"
                else:  # casual
                    prompt = f"Make this text more casual and friendly: {text}"

                enhanced_result = None

                for model in models_to_try:
                    print(f"\n🚀 Trying model: {model}")
                    try:
                        if model == "google/flan-t5-base":
                            payload = {
                                "inputs": prompt,
                                "parameters": {
                                    "max_length": 128,
                                    "temperature": 0.3
                                },
                                "options": {"wait_for_model": True}
                            }

                        elif model == "facebook/bart-large-cnn":
                            payload = {
                                "inputs": f"Rewrite in {enhancement_type} tone: {text}",
                                "parameters": {
                                    "max_length": len(text) + 30,
                                    "min_length": max(10, len(text) - 10)
                                },
                                "options": {"wait_for_model": True}
                            }

                        else:  # gpt2
                            payload = {
                                "inputs": f"{prompt}\nOriginal: {text}\nRewritten:",
                                "parameters": {
                                    "max_length": len(prompt) + len(text) + 50,
                                    "temperature": 0.7,
                                    "do_sample": True,
                                    "pad_token_id": 50256
                                },
                                "options": {"wait_for_model": True}
                            }

                        print(f"🧠 Payload for {model}: {payload}")
                        response = AIService.call_huggingface_api(model, payload)
                        print(f"🧾 HF API Response for {model}: {response}")

                        if response:
                            parsed = AIService.process_enhancement_response(response, text, prompt)
                            if parsed and parsed != text:
                                enhanced_result = parsed
                                print(f"✅ Successfully enhanced with {model}: '{enhanced_result}'")
                                break

                    except Exception as e:
                        print(f"❌ Error with model {model}: {e}")
                        continue

                if enhanced_result:
                    return enhanced_result

                print("⚠️ All model attempts failed, using rule-based fallback")
                return AIService.rule_based_enhancement(text, enhancement_type)

            else:
                print(f"❌ Unknown enhancement type: '{enhancement_type}'")
                return text

        except Exception as e:
            logging.error(f"❌ Exception in enhance_message: {e}")
            return AIService.rule_based_enhancement(text, enhancement_type)


    @staticmethod
    def rule_based_enhancement(text, enhancement_type):
        # Simplified fallback enhancement
        enhanced = text.strip()
        if enhanced and not enhanced[0].isupper():
            enhanced = enhanced[0].upper() + enhanced[1:]
        if enhanced and enhanced[-1] not in '.!?':
            enhanced += '.'
        if enhancement_type == "professional":
            enhanced = enhanced.replace("hey", "hello").replace("boss", "manager")
        elif enhancement_type == "casual":
            enhanced = enhanced.replace("please", "hey").replace("kindly", "just")
        return enhanced

    @staticmethod 
    def fix_basic_grammar(text):
        """Fix basic grammar issues"""
        try:
            # Fix double modals like "could be might"
            text = re.sub(r'\b(could|would|should|might|may|will|can)\s+(be\s+)?(might|may|could|would|should|will|can)\b', 
                        r'\1 \2', text, flags=re.IGNORECASE)
            
            # Fix "could be might" specifically -> "could be" or "might be"
            text = re.sub(r'\bcould\s+be\s+might\b', 'might be', text, flags=re.IGNORECASE)
            text = re.sub(r'\bmight\s+be\s+could\b', 'could be', text, flags=re.IGNORECASE)
            
            # Fix double spacing
            text = re.sub(r'\s+', ' ', text)
            
            # Fix capitalization at start
            text = text.strip()
            if text and not text[0].isupper():
                text = text[0].upper() + text[1:]
                
            return text
            
        except Exception as e:
            logging.error(f"Error fixing basic grammar: {e}")
            return text

    # @staticmethod  
    # def call_huggingface_api(model_name, payload):
    #     """Enhanced API call with better error handling"""
    #     HF_API_URL = "https://api-inference.huggingface.co/models"
    #     headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    #     try:
    #         print(f"Making API call to: {HF_API_URL}/{model_name}")
    #         response = requests.post(
    #             f"{HF_API_URL}/{model_name}", 
    #             headers=headers, 
    #             json=payload, 
    #             timeout=30
    #         )

    #         print(f"API Response Status: {response.status_code}")
    #         print(f"API Response Text: {response.text}")

    #         if response.status_code == 503:
    #             # Model is loading, wait and retry
    #             print("Model is loading, waiting 10 seconds...")
    #             import time
    #             time.sleep(10)
    #             response = requests.post(
    #                 f"{HF_API_URL}/{model_name}", 
    #                 headers=headers, 
    #                 json=payload, 
    #                 timeout=30
    #             )

    #         if response.status_code != 200:
    #             logging.error(f"Hugging Face API returned {response.status_code}: {response.text}")
    #             return None

    #         result = response.json()
    #         print(f"API Response JSON: {result}")
    #         return result
            
    #     except requests.exceptions.Timeout:
    #         logging.error("Hugging Face API request timed out")
    #         return None
    #     except requests.exceptions.RequestException as e:
    #         logging.error(f"Request error: {e}")
    #         return None
    #     except json.JSONDecodeError as e:
    #         logging.error(f"JSON decode error: {e}")
    #         return None
    #     except Exception as e:
    #         logging.error(f"Failed to call Hugging Face API: {e}")
    #         return None
    # @staticmethod
    # def rule_based_enhancement(text, enhancement_type):
    #     """Fallback rule-based text enhancement"""
    #     try:
    #         if enhancement_type == "professional":
    #             # Make text more formal
    #             enhanced = text.strip()
                
    #             # Replace casual words with formal ones
    #             replacements = {
    #                 "hey": "Hello",
    #                 "hi": "Hello",
    #                 "yeah": "Yes",
    #                 "yep": "Yes",
    #                 "nope": "No",
    #                 "gonna": "going to",
    #                 "wanna": "want to",
    #                 "gotta": "have to",
    #                 "kinda": "kind of",
    #                 "sorta": "sort of",
    #                 "ok": "Okay",
    #                 "u": "you",
    #                 "ur": "your",
    #                 "r": "are",
    #                 "thx": "Thank you",
    #                 "thanks": "Thank you"
    #             }
                
    #             words = enhanced.split()
    #             for i, word in enumerate(words):
    #                 lower_word = word.lower().strip('.,!?')
    #                 if lower_word in replacements:
    #                     # Preserve punctuation
    #                     punct = ''.join(c for c in word if c in '.,!?')
    #                     words[i] = replacements[lower_word] + punct
                
    #             enhanced = ' '.join(words)
                
    #             # Ensure proper capitalization
    #             if enhanced and not enhanced[0].isupper():
    #                 enhanced = enhanced[0].upper() + enhanced[1:]
                
    #             # Add period if missing
    #             if enhanced and enhanced[-1] not in '.!?':
    #                 enhanced += '.'
                    
    #             return enhanced
                
    #         elif enhancement_type == "casual":
    #             # Make text more casual
    #             enhanced = text.strip()
                
    #             # Replace formal words with casual ones
    #             replacements = {
    #                 "Hello": "Hey",
    #                 "Greetings": "Hi",
    #                 "Yes": "Yeah",
    #                 "No": "Nope",
    #                 "going to": "gonna",
    #                 "want to": "wanna",
    #                 "have to": "gotta",
    #                 "kind of": "kinda",
    #                 "sort of": "sorta",
    #                 "Thank you": "Thanks",
    #                 "you are": "you're",
    #                 "I am": "I'm",
    #                 "cannot": "can't",
    #                 "will not": "won't",
    #                 "should not": "shouldn't"
    #             }
                
    #             for formal, casual in replacements.items():
    #                 enhanced = enhanced.replace(formal, casual)
                
    #             # Remove overly formal punctuation
    #             if enhanced.endswith('.') and not enhanced.endswith('...'):
    #                 enhanced = enhanced[:-1]
                    
    #             return enhanced
            
    #         else:
    #             return text
                
    #     except Exception as e:
    #         logging.error(f"Error in rule-based enhancement: {e}")
    #         return text
    @staticmethod
    def detect_language(text):
        """Detect language of the message"""
        try:
            # Simple language detection based on common words
            spanish_words = ['hola', 'como', 'que', 'es', 'el', 'la', 'de', 'y']
            french_words = ['bonjour', 'comment', 'que', 'est', 'le', 'la', 'de', 'et']
            german_words = ['hallo', 'wie', 'was', 'ist', 'der', 'die', 'das', 'und']
            
            text_lower = text.lower()
            
            spanish_count = sum(1 for word in spanish_words if word in text_lower)
            french_count = sum(1 for word in french_words if word in text_lower)
            german_count = sum(1 for word in german_words if word in text_lower)
            
            if spanish_count > 1:
                return 'es'
            elif french_count > 1:
                return 'fr'
            elif german_count > 1:
                return 'de'
            else:
                return 'en'
            
        except Exception as e:
            logging.error(f"Error detecting language: {e}")
            return 'en'

# Store messages in memory for AI processing (supplement to database)
chat_message_cache = {}


def get_recent_messages(chat_id, limit=10):
    """
    Get recent messages for smart reply generation
    Should return messages in format expected by smart_reply_suggestions
    """
    try:
        # Example implementation - adjust based on your database schema
        cursor = connection.cursor(dictionary=True)
        sql_query = """
            SELECT * FROM chatmessage
            WHERE chat_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        cursor.execute(sql_query, (chat_id, limit))
        messages = cursor.fetchall()
        
        # Convert to format expected by smart_reply_suggestions
        message_history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            message_history.append({
                'message': msg.content,  # Adjust field name based on your schema
                'sender_id': msg.sender_id,
                'timestamp': msg.timestamp
            })
        
        return message_history
        
    except Exception as e:
        print(f"Error fetching recent messages: {e}")
        return []
    
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
        update_fields = []
        update_values = []
        image_data = profile_image.read() if profile_image else None
        update_fields.append("profile_image = %s")
        update_values.append(image_data)
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
        SELECT user_id FROM users WHERE email = %s
        """, (email1,))
        user1 = cursor.fetchone()

        cursor.execute("""
        SELECT user_id FROM users WHERE email = %s
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
        SELECT chat_id FROM chatsession WHERE 
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
            INSERT INTO chatsession (chat_id, user1_id, user2_id) VALUES (%s, %s, %s)
            """, (chat_id, user1_id, user2_id))
            conn.commit()
        # Join the room corresponding to the chat session
        join_room(chat_id)

        # Initialize message cache for this chat
        if chat_id not in chat_message_cache:
            chat_message_cache[chat_id] = []

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
    
    # Initialize message cache for this chat if not exists
    if chat_id not in chat_message_cache:
        chat_message_cache[chat_id] = []
    
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
        SELECT user_id FROM users WHERE email = %s
        """, (sender_email,))
        sender_ids = cursor.fetchone()
        sender_id = sender_ids[0]

        cursor.execute("""
        SELECT user_id FROM users WHERE email = %s
        """, (receiver_email,))
        receiver_ids = cursor.fetchone()
        receiver_id = receiver_ids[0]

        # AI Analysis
        sentiment = AIService.analyze_sentiment(message)
        language = AIService.detect_language(message)

        # Insert the message into the chatmessage table
        cursor.execute("""
        INSERT INTO chatmessage (message_id, chat_id, sender_id, receiver_id, message) VALUES (%s, %s, %s, %s, %s)
        """, (message_id, chat_id, sender_id, receiver_id, message))
        conn.commit()

        # Optionally handle image data
        if image:
            cursor.execute("""
            INSERT INTO ChatMessageImages (message_id, chat_id, sender_id, file_name, file_type, file_url) VALUES (%s, %s, %s, %s, %s, %s)
            """, (message_id, chat_id, sender_id, image['file_name'], image['file_type'], image['file_data']))
            conn.commit()

        # Create message object with AI analysis
        message_obj = {
            'message_id': message_id,
            'chat_id': chat_id,
            'sender_id': sender_id,
            'sender_email': sender_email,
            'receiver_id': receiver_id,
            'receiver_email': receiver_email,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'ai_analysis': {
                'sentiment': sentiment,
                'language': language
            }
        }

        # Add to message cache for AI processing
        if chat_id not in chat_message_cache:
            chat_message_cache[chat_id] = []
        chat_message_cache[chat_id].append(message_obj)

        # Keep only last 50 messages in cache
        if len(chat_message_cache[chat_id]) > 50:
            chat_message_cache[chat_id] = chat_message_cache[chat_id][-50:]

        # Example logging
        logging.info("Emitting new message with AI analysis: %s", message_obj)
        
        emit('new_message', message_obj, room=chat_id)

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
        SELECT cm.message_id, cm.sender_id, cm.receiver_id, cm.message, cm.timestamp, u.email as sender_email
        FROM chatmessage cm
        JOIN users u ON cm.sender_id = u.user_id
        WHERE cm.chat_id = %s ORDER BY cm.timestamp ASC
        """, (chat_id,))

        messages = cursor.fetchall()

        # Add AI analysis to each message and update cache
        processed_messages = []
        chat_message_cache[chat_id] = []

        for message in messages:
            if isinstance(message['timestamp'], datetime):
                message['timestamp'] = message['timestamp'].isoformat()
            
            # Add AI analysis
            sentiment = AIService.analyze_sentiment(message['message'])
            language = AIService.detect_language(message['message'])
            
            message['ai_analysis'] = {
                'sentiment': sentiment,
                'language': language
            }
            
            processed_messages.append(message)
            chat_message_cache[chat_id].append(message)

        emit('messages_fetched', {'messages': processed_messages})

    except mysql.connector.Error as e:
        logging.error("Database error: %s", e)
        emit('error', {'message': 'An error occurred while fetching messages.'})
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        emit('error', {'message': 'An unexpected error occurred.'})

@socketio.on('get_smart_replies')
def handle_get_smart_replies(data):
    try:
        chat_id = data.get('chat_id')
        print(chat_id)
        # Get recent message history
        recent_messages = get_recent_messages(chat_id, limit=5)
        
        # Generate smart replies
        smart_replies = AIService.smart_reply_suggestions(recent_messages,3)
        
        # Emit back to the requesting user
        emit('smart_replies_generated', {
            'suggestions': smart_replies,
            'chat_id': chat_id
        })
        
    except Exception as e:
        print(f"Error generating smart replies: {e}")
        emit('smart_replies_generated', {'suggestions': []})


@socketio.on('translate_message')
def handle_translate_message(data):
    print("=== BACKEND: translate_message RECEIVED ===")
    print(f"Data: {data}")

    text = data.get('text')
    target_language = data.get('target_language', 'es')
    print(target_language)
    if not text:
        print("❌ No text provided for translation.")
        emit('error', {'message': 'Text is required for translation.'})
        return

    print(f"📤 Translating text: '{text}' to language: '{target_language}'")

    try:
        translated = AIService.translate_message(text, target_language)
        print(f"✅ Translated result: '{translated}'")

        emit('message_translated', {
            'original': text,
            'translated': translated,
            'language': target_language
        })

    except Exception as e:
        logging.error(f"❌ Error translating message: {e}")
        print(f"❌ Exception occurred: {e}")
        emit('message_translated', {
            'original': text,
            'translated': text,  # Fallback
            'language': target_language
        })

@socketio.on('enhance_message')
def handle_enhance_message(data):
    print("=== BACKEND: enhance_message RECEIVED ===")
    print(f"Data: {data}")

    text = data.get('text')
    enhancement_type = data.get('type', 'grammar')
    print(f"Enhancement Type: {enhancement_type}")

    if not text:
        print("❌ No text provided for enhancement.")
        emit('error', {'message': 'Text is required for enhancement.'})
        return

    print(f"📤 Enhancing text: '{text}' with type: '{enhancement_type}'")

    try:
        enhanced = AIService.enhance_message(text, enhancement_type)
        print(f"✅ Enhanced result: '{enhanced}'")

        emit('message_enhanced', {
            'original': text,
            'enhanced': enhanced,
            'type': enhancement_type
        })

    except Exception as e:
        logging.error(f"❌ Error enhancing message: {e}")
        print(f"❌ Exception occurred: {e}")
        emit('message_enhanced', {
            'original': text,
            'enhanced': text,  # Fallback to original
            'type': enhancement_type
        })

@socketio.on('summarize_conversation')
def handle_summarize_conversation(data):
    chat_id = data.get('chat_id')
    
    if not chat_id:
        emit('error', {'message': 'Chat ID is required.'})
        return
    
    try:
        messages = chat_message_cache.get(chat_id, [])
        summary = AIService.summarize_conversation(messages)
        emit('conversation_summarized', {'summary': summary})
    except Exception as e:
        logging.error(f"Error summarizing conversation: {e}")
        emit('conversation_summarized', {'summary': 'Unable to generate summary'})

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
    
    cursor.execute("SELECT username, email, profile_image FROM users WHERE email = %s", (email,))
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
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
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
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    user_result = cursor.fetchone()
    
    if not user_result:
        return jsonify({"error": "User not found"}), 404
        
    user_id = user_result[0]
    update_values.append(user_id)  # For WHERE clause

    sql_update = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"

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
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
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
            FROM chatmessage cm
            JOIN (
                SELECT chat_id, MAX(timestamp) as max_time
                FROM chatmessage
                GROUP BY chat_id
            ) latest ON cm.chat_id = latest.chat_id AND cm.timestamp = latest.max_time
            JOIN chatsession cs ON cs.chat_id = cm.chat_id
            JOIN users u ON (u.user_id = cs.user1_id OR u.user_id = cs.user2_id)
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
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        user_id = user_result['user_id']
        
        # Get all contacts for this user
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, u.profile_image 
            FROM contact c
            JOIN users u ON c.contact_user_id = u.user_id
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
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return jsonify({'status': 'error', 'message': 'One or both users not found'}), 404
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Check if the contact already exists
        cursor.execute("""
            SELECT contact_id FROM contact
            WHERE user_id = %s AND contact_user_id = %s
        """, (user_id, contact_user_id))
        
        if cursor.fetchone():
            return jsonify({'status': 'error', 'message': 'Contact already exists'}), 409
            
        # Create contact in both directions for bidirectional relationship
        contact_id1 = str(uuid.uuid4())
        contact_id2 = str(uuid.uuid4())
        
        # Add first direction
        cursor.execute("""
            INSERT INTO contact (contact_id, user_id, contact_user_id)
            VALUES (%s, %s, %s)
        """, (contact_id1, user_id, contact_user_id))
        
        # Add second direction
        cursor.execute("""
            INSERT INTO contact (contact_id, user_id, contact_user_id)
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
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return jsonify({'status': 'error', 'message': 'One or both users not found'}), 404
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Remove contact in both directions
        cursor.execute("""
            DELETE FROM contact
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
