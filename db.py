import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
from psycopg2 import sql


def connect_to_rds():
    try:
        conn = psycopg2.connect(
            host=os.getenv('HOST'),
            database=os.getenv('DATABASE'),
            user=os.getenv('DB_USER'),
            password=os.getenv('PASSWORD'),
            port="5432"
        )
        print("Connected to RDS")
        return conn
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        return None

# Function to save user folder path to the database
def save_user_folder_path(user_name, folder_path, db_conn):
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_folder (user_name, folder_path) VALUES (%s, %s) ON CONFLICT (user_name) DO UPDATE SET folder_path = %s",
                (user_name, folder_path, folder_path)  # Insert or update if user already has a folder path
            )
            db_conn.commit()
            print(f"User {user_name}'s folder path saved/updated successfully.")
    except Exception as e:
        print(f"Error saving folder path for user {user_name}: {e}")
        db_conn.rollback()

# connection = connect_to_rds()

# def print_table_details(table_name):
#     """
#     Connect to the database and print the details of a specific table.
#     :param db_config: Dictionary containing database connection details.
#     :param table_name: Name of the table to retrieve details for.
#     """
#     try:
        
#         cur = connection.cursor()
        
#         # Fetch table schema details
#         query = sql.SQL("""
#             SELECT column_name, data_type, is_nullable, character_maximum_length
#             FROM information_schema.columns
#             WHERE table_name = %s;
#         """)
#         cur.execute(query, (table_name,))
#         rows = cur.fetchall()

#         # Print table details
#         print(f"Details for table: {table_name}")
#         print(f"{'Column Name':<20} {'Data Type':<20} {'Is Nullable':<15} {'Max Length':<10}")
#         print("-" * 65)
#         for row in rows:
#             column_name, data_type, is_nullable, max_length = row
#             print(f"{column_name:<20} {data_type:<20} {is_nullable:<15} {str(max_length):<10}")

#     except Exception as e:
#         print(f"Error: {e}")

# def fetch_records(table_name):
#     """
#     Connect to the database and fetch all records from the specified table.
#     :param db_config: Dictionary containing database connection details.
#     :param table_name: Name of the table to fetch records from.
#     """
#     try:
      
#         cur = connection.cursor()

#         # Query to fetch all records
#         query = f"SELECT * FROM {table_name} LIMIT 10;"  # Limit added to avoid timeouts
#         cur.execute(query)
#         rows = cur.fetchall()

#         # Fetch and print records
#         if rows:
#             print(f"Records from table '{table_name}':")
#             for row in rows:
#                 print(row)
#         else:
#             print(f"No records found in table '{table_name}'.")

#     except Exception as e:
#         print(f"Error: {e}")

# Save file tracking data to the database
def save_file_metadata(file_id, file_name, db_conn):
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO file_metadata (file_id, name) VALUES (%s, %s) ON CONFLICT (file_id) DO NOTHING",
                (file_id, file_name)
            )
            db_conn.commit()
            print(f"Saved metadata for file: {file_name}")
    except Exception as e:
        print(f"Error saving metadata: {e}")
        db_conn.rollback()

# def test():

    
#     # print_table_details('chat_history')
#     # print_table_details('user_folder')

#     # fetch_records('chat_history')
#     # fetch_records('user_folder')

#     if connection:
#         connection.close()
# test()

