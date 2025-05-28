import mysql.connector
import os
from dotenv import load_dotenv
import base64
from Auth import connection
import logging
from mysql.connector import Error

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
    try:
        if connection.is_connected():
            print("Connected to MySQL database")
            cursor = connection.cursor()

            # Check if 'user_id' column exists
            cursor.execute("SHOW COLUMNS FROM users LIKE 'user_id'")
            result = cursor.fetchone()
            if not result:
                print("Column 'user_id' not found in users table.")
                return []

            # Query all users
            sql_query = "SELECT user_id, username, email, profile_image FROM users"
            cursor.execute(sql_query)
            all_users = cursor.fetchall()

            users_list = []
            for user in all_users:
                user_id, username, email, profile_image = user
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

    except Error as e:
        print("Error while fetching users:", e)
        return []

# Call the function
All_Users()

# Add these functions to your existing API.py file



def All_Users():
    """Function to fetch all users from the database."""
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT user_id, username, email, profile_image
            FROM users
        """)
        users = cursor.fetchall()
        
        # Process the results
        processed_users = []
        for user in users:
            # Convert binary profile image to base64 string if it exists
            profile_image = None
            if user['profile_image']:
                profile_image = base64.b64encode(user['profile_image']).decode('utf-8')
                
            processed_users.append({
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'profile_image': profile_image
            })
            
        return processed_users
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return []
    finally:
        cursor.close()

def Get_User_Contacts(email):
    """Function to fetch all contacts for a specific user."""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user ID from email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return []
            
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
                profile_image = base64.b64encode(contact['profile_image']).decode('utf-8')
                
            processed_contacts.append({
                'user_id': contact['user_id'],
                'username': contact['username'],
                'email': contact['email'],
                'profile_image': profile_image
            })
            
        return processed_contacts
    except Exception as e:
        logging.error(f"Error fetching contacts: {e}")
        return []
    finally:
        cursor.close()

def Add_Contact(user_email, contact_email):
    """Function to add a contact for a user."""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user IDs from emails
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return {"status": "error", "message": "One or both users not found"}
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Check if the contact already exists
        cursor.execute("""
            SELECT contact_id FROM Contacts
            WHERE user_id = %s AND contact_user_id = %s
        """, (user_id, contact_user_id))
        
        if cursor.fetchone():
            return {"status": "error", "message": "Contact already exists"}
            
        # Create contact IDs
        import uuid
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
        
        return {"status": "success", "message": "Contact added successfully"}
        
    except Exception as e:
        connection.rollback()
        logging.error(f"Error adding contact: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()

def Remove_Contact(user_email, contact_email):
    """Function to remove a contact for a user."""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get user IDs from emails
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (contact_email,))
        contact_result = cursor.fetchone()
        
        if not user_result or not contact_result:
            return {"status": "error", "message": "One or both users not found"}
            
        user_id = user_result['user_id']
        contact_user_id = contact_result['user_id']
        
        # Remove contact in both directions
        cursor.execute("""
            DELETE FROM Contacts
            WHERE (user_id = %s AND contact_user_id = %s)
            OR (user_id = %s AND contact_user_id = %s)
        """, (user_id, contact_user_id, contact_user_id, user_id))
        
        rows_affected = cursor.rowcount
        connection.commit()
        
        if rows_affected > 0:
            return {"status": "success", "message": "Contact removed successfully"}
        else:
            return {"status": "error", "message": "Contact relationship not found"}
        
    except Exception as e:
        connection.rollback()
        logging.error(f"Error removing contact: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
      
