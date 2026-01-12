from minio import Minio
import os
import io

class MinIOStorage:
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )
        
        self.bucket_name = 'cdn-files'
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
    
    def get_file(self, file_name: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket_name, file_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            raise FileNotFoundError(f"File {file_name} not found: {str(e)}")
    
    def put_file(self, file_name: str, content: bytes):
        self.client.put_object(
            self.bucket_name,
            file_name,
            io.BytesIO(content),
            len(content)
        )
    
    def delete_file(self, file_name: str):
        self.client.remove_object(self.bucket_name, file_name)
    
    def list_files(self):
        objects = self.client.list_objects(self.bucket_name, recursive=True)
        return [obj.object_name for obj in objects]
