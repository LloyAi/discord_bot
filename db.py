import psycopg2
import os

def connect_to_rds():
    try:
        conn = psycopg2.connect(
            host=os.getenv('HOST'),
            database=os.getenv('DATABASE'),
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            port="5432"
        )
        print("Connected to RDS")
        return conn
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        return None

connection = connect_to_rds()
if connection:
    connection.close()
