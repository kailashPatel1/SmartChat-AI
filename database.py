import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smartchat.db')

def get_db_connection():
    """Establishes and returns a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the ChatHistory table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def save_chat(user_message, bot_response):
    """Saves a single interaction to the ChatHistory table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ChatHistory (user_message, bot_response)
            VALUES (?, ?)
        ''', (user_message, bot_response))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving chat to database: {e}")
        return False

def get_chat_history(limit=50):
    """Retrieves the recent chat logs from the database, ordered by timestamp ascending."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Retrieve ordered by timestamp ascending so it reads like a standard chat script
        cursor.execute('''
            SELECT id, user_message, bot_response, timestamp
            FROM ChatHistory
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert sqlite3.Row objects to dictionaries
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'user_message': row['user_message'],
                'bot_response': row['bot_response'],
                'timestamp': row['timestamp']
            })
        return history
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return []

def clear_chat_history():
    """Clears all records in the ChatHistory table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ChatHistory')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return False

def delete_conversation_by_message(user_message):
    """Deletes all records matching a specific user message from the ChatHistory table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ChatHistory WHERE user_message = ?', (user_message,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting chat conversation: {e}")
        return False

def check_conversation_exists(conversation_id):
    """Checks if a conversation exists in the database by id."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM ChatHistory WHERE id = ?', (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        print(f"Error checking conversation existence: {e}")
        return False

def delete_conversation_by_id(conversation_id):
    """Deletes a single conversation row by its database id."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ChatHistory WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting conversation by id: {e}")
        return False

if __name__ == '__main__':
    # Initialize the database if run directly
    init_db()
