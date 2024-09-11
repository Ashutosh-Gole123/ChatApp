import mysql.connector
import os
from dotenv import load_dotenv
import base64

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

def All_Users():
    if connection.is_connected():
        print("Connected to MySQL database")
            
        cursor = connection.cursor()
        # SQL query to fetch all users' details
        sql_query = "SELECT user_id, username, email, profile_image FROM Users"
        cursor.execute(sql_query)
        
        # Fetch all user data
        all_users = cursor.fetchall()
        
        users_list = []
        for user in all_users:
            user_id, username, email, profile_image = user
            # Convert the binary image data to base64
            profile_image_base64 = None
            if profile_image:
                profile_image_base64 = base64.b64encode(profile_image).decode('utf-8')
            
            
            users_list.append({
                "user_id": user_id,
                "username": username,
                "email": email,
                "profile_image": profile_image_base64
            })
            
        return users_list

All_Users()
      
