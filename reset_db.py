import db_utils
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    try:
        # Connect without specifying a database
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD') or None
        )
        
        cursor = connection.cursor()
        
        # Drop the database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {os.getenv('DB_NAME')}")
        print(f"Dropped database {os.getenv('DB_NAME')}")
        
        # Recreate the database
        cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME')}")
        print(f"Created database {os.getenv('DB_NAME')}")
        
        # Reinitialize the database
        if db_utils.init_db():
            print("Database initialized successfully!")
        else:
            print("Failed to initialize database.")
            
    except Error as e:
        print(f"Error resetting database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    confirm = input("This will delete all data. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled.")
