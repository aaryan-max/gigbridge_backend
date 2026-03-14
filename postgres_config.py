"""
PostgreSQL database configuration for GigBridge
Replaces SQLite with PostgreSQL while maintaining all existing functionality
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.errors

# PostgreSQL Connection Configuration
# Set these environment variables or modify the defaults below
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'gigbridge'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'sarthak123'),
}

def get_postgres_connection():
    """Get a PostgreSQL connection using environment variables"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.OperationalError as e:
        print(f"PostgreSQL connection error: {e}")
        print("Please ensure PostgreSQL is running and configuration is correct:")
        print(f"Host: {POSTGRES_CONFIG['host']}")
        print(f"Port: {POSTGRES_CONFIG['port']}")
        print(f"Database: {POSTGRES_CONFIG['database']}")
        print(f"User: {POSTGRES_CONFIG['user']}")
        raise

def client_db():
    """Return connection to client database (same PostgreSQL database)"""
    return get_postgres_connection()

def freelancer_db():
    """Return connection to freelancer database (same PostgreSQL database)"""
    return get_postgres_connection()

# PostgreSQL-specific error handling
def is_column_exists_error(error):
    """Check if error is for duplicate column (PostgreSQL)"""
    return isinstance(error, psycopg2.errors.DuplicateColumn)

def is_table_exists_error(error):
    """Check if error is for duplicate table (PostgreSQL)"""
    return isinstance(error, psycopg2.errors.DuplicateTable)

def is_unique_violation_error(error):
    """Check if error is for unique constraint violation"""
    return isinstance(error, psycopg2.errors.UniqueViolation)

# PostgreSQL data type conversions
def convert_sqlite_to_postgres_type(sqlite_type):
    """Convert SQLite data types to PostgreSQL equivalents"""
    type_mapping = {
        'INTEGER PRIMARY KEY AUTOINCREMENT': 'SERIAL PRIMARY KEY',
        'INTEGER PRIMARY KEY': 'SERIAL PRIMARY KEY',
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT',
        'REAL': 'REAL',
        'BLOB': 'BYTEA',
        'TIMESTAMP': 'TIMESTAMP',
        'BOOLEAN': 'BOOLEAN'
    }
    return type_mapping.get(sqlite_type.upper(), sqlite_type)

# Row factory for dictionary-like access (similar to SQLite's row_factory)
def get_dict_cursor(connection):
    """Get cursor that returns rows as dictionaries"""
    return connection.cursor(cursor_factory=RealDictCursor)
