import mysql.connector
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

HOST_NAME = os.getenv('HOST_NAME')
USER_NAME = os.getenv('USER_NAME')
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')
# Establish a database connection (this can be moved to a config or utility file if needed)
connection = mysql.connector.connect(
    host=HOST_NAME,
    user=USER_NAME,
    passwd=PASSWORD,
    database=DATABASE
)

def register_user(username, password, email, profile_image=None):
    """Register a new user in the Users table."""
    if connection.is_connected():
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        sql_query = """
            INSERT INTO users (username, password_hash, email, profile_image)
            VALUES (%s, %s, %s, %s)
            """
            
        cursor = connection.cursor()
        cursor.execute(sql_query, (username, password_hash, email, profile_image))
        connection.commit()
        
        return {"status": "User registered successfully"}

    else:
        return {"status": "Error connecting to the database"}

# Function to login a user
def login_user(username, password):
    if connection.is_connected():
        cursor = connection.cursor()
            
            # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

            # SQL query to verify user credentials
        sql_query = """
            SELECT * FROM users WHERE email = %s AND password_hash = %s
            """
            
        cursor.execute(sql_query, (username, password_hash))
        user = cursor.fetchone()
            
        if user:
            return {"status": "success", "message": "Login successful"}
        else:
            return {"status": "error", "message": "Invalid username or password"}
    
    