import sqlite3
from datetime import datetime

class MusicDatabase:
    def __init__(self, database_name="music_database.db"):
        self.connection = sqlite3.connect(database_name)
        self.create_tables()

    def create_tables(self):
        with self.connection:
            cursor = self.connection.cursor()
            
            # Table for storing song requests
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS song_request (
                    user_id BIGINT,
                    guild_id BIGINT,
                    youtube_title TEXT,
                    youtube_url TEXT,
                    executed_at TIMESTAMP NOT NULL
                )
            ''')

    def add_song_request(self, user_id, guild_id, youtube_title, youtube_url):
        with self.connection:
            cursor = self.connection.cursor()
            played_at = datetime.now()
            cursor.execute('''
                INSERT INTO song_request (user_id, guild_id, youtube_title, youtube_url, played_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, guild_id, youtube_title, youtube_url, played_at))

    def read_all_song_requests_for_guild_id(self, guild_id):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM song_request
                WHERE guild_id = ?
            ''', (guild_id,))
            return cursor.fetchall()
        
    def get_users_recent_requests(self, user_id):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT youtube_title FROM song_request
                WHERE user_id = ?
                ORDER BY executed_at ASC
            ''', (user_id,))
            return cursor.fetchall()

    def get_guild_history_recent(self, guild_id: int):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT user_id, played_at FROM song_request
                WHERE guild_id = ? 
                ORDER BY executed_at ASC
                ''', [guild_id])
            return cursor.fetchall()

    def close_connection(self):
        self.connection.close()