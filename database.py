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
                    id SERIAL INT PRIMARY KEY,
                    user_id BIGINT,
                    guild_id BIGINT,
                    youtube_title TEXT,
                    youtube_url TEXT,
                    executed_at TIMESTAMP NOT NULL,
                    spotify_url TEXT
                )
            ''')

            #Create a table that stores the number of plays per user
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_play_count (
                    user_id BIGINT,
                    guild_id BIGINT,
                    play_count INT
                )
            ''')

        # Now write helper methods to add and get the user_play_count
    def add_play_count(self, user_id, guild_id):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO user_play_count (user_id, guild_id, play_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET play_count = play_count + 1
            ''', (user_id, guild_id))

    def get_play_count(self, user_id, guild_id):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT play_count FROM user_play_count
                WHERE user_id = ? AND guild_id = ?
            ''', (user_id, guild_id))
            result = cursor.fetchone()
            if result is None:
                return 0
            return result[0]




    def add_song_request(self, user_id, guild_id, youtube_title, youtube_url, spotify_url=None):
        with self.connection:
            cursor = self.connection.cursor()
            played_at = datetime.now()
            cursor.execute('''
                INSERT INTO song_request (user_id, guild_id, youtube_title, youtube_url, executed_at, spotify_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, guild_id, youtube_title, youtube_url, played_at, spotify_url))

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