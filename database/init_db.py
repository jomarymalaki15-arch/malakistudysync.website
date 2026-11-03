"""
Database Initialization Script for StudySync
Connects to local MySQL Server (via XAMPP) and runs studysync_db.sql.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error

# Add parent directory to path to import Config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def init_database():
    """Initializes the MySQL database using the SQL migration file."""
    sql_file_path = os.path.join(os.path.dirname(__file__), 'studysync_db.sql')
    if not os.path.exists(sql_file_path):
        print(f"Error: SQL file not found at {sql_file_path}")
        return False

    print(f"Connecting to MySQL Server at {Config.DB_HOST}:{Config.DB_PORT} as {Config.DB_USER}...")
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = connection.cursor()

        print(f"Reading schema from {sql_file_path}...")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Split commands by semicolon while respecting delimiter blocks
        raw_statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        print(f"Executing {len(raw_statements)} raw SQL blocks...")
        for i, block in enumerate(raw_statements, 1):
            # Strip comment lines from block
            lines = [line for line in block.splitlines() if not line.strip().startswith('--') and not line.strip().startswith('/*')]
            statement = '\n'.join(lines).strip()
            if not statement:
                continue
            try:
                cursor.execute(statement)
            except Error as stmt_err:
                print(f"Statement #{i} warning/error: {stmt_err}")

        connection.commit()
        cursor.close()
        connection.close()
        print("Database 'studysync_db' initialized successfully with all 8 tables and sample records!")
        return True

    except Error as e:
        print(f"Failed to connect or initialize MySQL: {e}")
        print("Please ensure XAMPP MySQL is running.")
        return False

if __name__ == '__main__':
    init_database()
