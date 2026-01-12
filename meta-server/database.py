import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Tuple, Optional

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        database_url = os.getenv('DATABASE_URL', 'postgresql://cdn_user:cdn_pass@postgres:5432/cdn_metadata')
        self.connection = psycopg2.connect(database_url)
        self.connection.autocommit = True
    
    def get_cursor(self):
        return self.connection.cursor(cursor_factory=RealDictCursor)
    
    def register_cdn(self, address: str, lat: float, lng: float) -> int:
        cursor = self.get_cursor()
        cursor.execute(
            "INSERT INTO cdn_nodes (address, lat, lng) VALUES (%s, %s, %s) RETURNING id",
            (address, lat, lng)
        )
        result = cursor.fetchone()
        cursor.close()
        return result['id']
    
    def get_cdn_by_id(self, cdn_id: int) -> Optional[dict]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM cdn_nodes WHERE id = %s", (cdn_id,))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def get_all_cdns(self) -> List[dict]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM cdn_nodes")
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def add_or_update_file(self, file_name: str, file_hash: str, timestamp: int):
        cursor = self.get_cursor()
        cursor.execute(
            """INSERT INTO files (name, hash, timestamp) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (name) DO UPDATE 
               SET hash = EXCLUDED.hash, timestamp = EXCLUDED.timestamp""",
            (file_name, file_hash, timestamp)
        )
        cursor.execute(
            """INSERT INTO file_timestamps (file_name, timestamp) 
               VALUES (%s, %s) 
               ON CONFLICT (file_name) DO UPDATE 
               SET timestamp = EXCLUDED.timestamp""",
            (file_name, timestamp)
        )
        cursor.close()
    
    def get_file(self, file_name: str) -> Optional[dict]:
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM files WHERE name = %s", (file_name,))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def delete_file(self, file_name: str):
        cursor = self.get_cursor()
        cursor.execute("DELETE FROM files WHERE name = %s", (file_name,))
        cursor.close()
    
    def add_cdn_file_mapping(self, file_name: str, cdn_id: int):
        cursor = self.get_cursor()
        cursor.execute(
            """INSERT INTO cdn_file_mappings (file_name, cdn_id) 
               VALUES (%s, %s) 
               ON CONFLICT (file_name, cdn_id) DO NOTHING""",
            (file_name, cdn_id)
        )
        cursor.close()
    
    def get_cdns_with_file(self, file_name: str) -> List[int]:
        cursor = self.get_cursor()
        cursor.execute(
            "SELECT cdn_id FROM cdn_file_mappings WHERE file_name = %s",
            (file_name,)
        )
        results = cursor.fetchall()
        cursor.close()
        return [r['cdn_id'] for r in results]
    
    def remove_cdn_file_mapping(self, file_name: str, cdn_id: int):
        cursor = self.get_cursor()
        cursor.execute(
            "DELETE FROM cdn_file_mappings WHERE file_name = %s AND cdn_id = %s",
            (file_name, cdn_id)
        )
        cursor.close()
    
    def close(self):
        if self.connection:
            self.connection.close()
