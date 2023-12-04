import sqlite3

class DatabaseManager:
    def __init__(self, db_filename):
        self.db_filename = db_filename

    def init_db(self):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS users 
                           (id INTEGER PRIMARY KEY, username TEXT, name TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS messages 
                           (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT,
                           FOREIGN KEY (user_id) REFERENCES users (id))''')
            conn.commit()

    def add_user(self, username, name):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cur.fetchone() is not None:
                return "Пользователь с таким именем уже существует."
            
            cur.execute("INSERT INTO users (username, name) VALUES (?, ?)", (username, name))
            conn.commit()
            return "Пользователь добавлен"

    def delete_user(self, username):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()

            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
            if user is None:
                return "Пользователь не найден"

            cur.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return "Пользователь удален"
        
    def get_all_users(self):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            return users
    
    def get_titles(self, user_id):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title FROM messages WHERE user_id = ?", (user_id,))
            return cur.fetchall()
        
    def add_message(self, user_id, title, content):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO messages (user_id, title, content) VALUES (?, ?, ?)", 
                        (user_id, title, content))
            conn.commit()
    
    def get_messages(self, user_id):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT title, content FROM messages WHERE user_id = ?", (user_id,))
            return cur.fetchall()
    
    def get_titles_for_editing(self, user_id):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title FROM messages WHERE user_id = ?", (user_id,))
            return cur.fetchall()

    def get_message_title(self, message_id):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("SELECT title FROM messages WHERE id = ?", (message_id,))
            return cur.fetchone()

    def update_message_content(self, message_id, new_content):
        with sqlite3.connect(self.db_filename) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, message_id))
            conn.commit()
        
        
        
        
        
        
        
        
        
        