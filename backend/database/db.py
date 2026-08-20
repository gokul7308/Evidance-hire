import sqlite3
import os
from backend.config import Config

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    
    # We will define the full schema here as we implement more features
    schema = """
    CREATE TABLE IF NOT EXISTS system_info (
        id INTEGER PRIMARY KEY,
        version TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(schema)
        
        # Insert a version record if not exists
        cursor.execute("SELECT COUNT(*) FROM system_info")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO system_info (version) VALUES ('1.0.0')")
            
        conn.commit()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {Config.DB_PATH}")
