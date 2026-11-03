"""
StudySync Database Service
Handles connection pooling, query execution, transaction management,
and automatic resource cleanup for MySQL through XAMPP.
"""

import mysql.connector
from mysql.connector import pooling, Error
from config import Config
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Connection pool instance
_connection_pool = None

def get_connection_pool():
    """Initializes and returns a singleton connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="studysync_pool",
                pool_size=10,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=False
            )
            logger.info("Database connection pool established successfully.")
        except Error as e:
            logger.error(f"Error initializing database pool: {e}")
            raise
    return _connection_pool

def get_db_connection():
    """
    Retrieves a connection from the pool.
    Falls back to direct connection if pool fails.
    """
    try:
        pool = get_connection_pool()
        connection = pool.get_connection()
        return connection
    except Error as e:
        logger.warning(f"Connection pool acquisition failed, attempting direct connection: {e}")
        try:
            connection = mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=False
            )
            return connection
        except Error as err:
            logger.critical(f"Critical Database Connection Failure: {err}")
            raise

def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False, return_last_id=False):
    """
    Executes a parameterized SQL query safely.
    
    :param sql: SQL query string with %s placeholders
    :param params: Tuple or dict of parameters for the query
    :param fetchone: If True, returns a single dictionary row
    :param fetchall: If True, returns a list of dictionary rows
    :param commit: If True, commits the transaction
    :param return_last_id: If True, returns the generated AUTO_INCREMENT id
    :return: Query results or last inserted ID
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        # dictionary=True returns rows as dicts {col_name: value}
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(sql, params or ())
        
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
            
        if commit:
            connection.commit()
            if return_last_id:
                result = cursor.lastrowid
                
        return result
    except Error as err:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
        logger.error(f"SQL execution error on statement '{sql[:60]}...': {err}")
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass

def log_activity(user_id, action, details=None, ip_address="127.0.0.1"):
    """Logs user and system actions into the activity_logs table."""
    try:
        execute_query(
            "INSERT INTO activity_logs (user_id, action, ip_address, details) VALUES (%s, %s, %s, %s)",
            (user_id, action, ip_address, details),
            commit=True
        )
    except Exception as e:
        logger.warning(f"Could not log activity '{action}': {e}")
