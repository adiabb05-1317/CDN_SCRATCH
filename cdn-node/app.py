from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import redis
from minio import Minio
import httpx
import os
import io
from cache import LRUCache
from models import FilePutRequest

app = FastAPI()

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
META_SERVER_URL = os.getenv('META_SERVER_URL', 'http://meta-server:8002')
FSS_URL = os.getenv('FSS_URL', 'http://fss:5000')
CDN_ID = int(os.getenv('CDN_ID', 1))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)
local_cache = LRUCache(max_size=10 * 1024 * 1024)

BUCKET_NAME = 'cdn-files'

@app.on_event("startup")
async def startup_event():
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
    
    # Register with Meta Server
    try:
        async with httpx.AsyncClient() as client:
            register_payload = {
                "Type": 0,
                "IP": "localhost:4000",
                "Lat": float(os.getenv('CDN_LAT', 37.7749)),
                "Lng": float(os.getenv('CDN_LNG', -122.4194))
            }
            response = await client.post(f"{META_SERVER_URL}/meta/register", json=register_payload)
            if response.status_code == 200:
                global CDN_ID
                CDN_ID = response.json()['cdn_id']
                print(f"Successfully registered CDN with ID: {CDN_ID}")
            else:
                print(f"Failed to register CDN: {response.text}")
    except Exception as e:
        print(f"Error registering CDN: {str(e)}")


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/cdn/cache/{file_path:path}", response_class=PlainTextResponse)
async def get_file(file_path: str):
    cache_key = f"cdn:{file_path}"
    
    cached_content = redis_client.get(cache_key)
    if cached_content:
        return cached_content.decode('utf-8')
    
    local_content = local_cache.get(file_path)
    if local_content:
        redis_client.set(cache_key, local_content)
        return local_content.decode('utf-8')
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FSS_URL}/get/{file_path}")
            if response.status_code == 200:
                content = response.text
                content_bytes = content.encode('utf-8')
                
                redis_client.set(cache_key, content_bytes)
                local_cache.put(file_path, content_bytes)
                
                async with httpx.AsyncClient() as meta_client:
                    await meta_client.post(
                        f"{META_SERVER_URL}/meta/update",
                        json={
                            "file_name": file_path,
                            "file_hash": "",
                            "timestamp": "0",
                            "cdn_id": CDN_ID
                        }
                    )
                
                return content
            else:
                raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/cdn/cache/{file_path:path}")
async def put_file(file_path: str, request: FilePutRequest):
    content_bytes = request.content.encode('utf-8')
    
    try:
        minio_client.put_object(
            BUCKET_NAME,
            file_path,
            io.BytesIO(content_bytes),
            len(content_bytes)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    
    cache_key = f"cdn:{file_path}"
    redis_client.set(cache_key, content_bytes)
    local_cache.put(file_path, content_bytes)
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{META_SERVER_URL}/meta/update",
            json={
                "file_name": file_path,
                "file_hash": request.file_hash,
                "timestamp": request.timestamp,
                "cdn_id": CDN_ID
            }
        )
    
    return {"status": "success", "file": file_path}

@app.delete("/cdn/cache/{file_path:path}")
async def delete_file(file_path: str):
    cache_key = f"cdn:{file_path}"
    redis_client.delete(cache_key)
    local_cache.delete(file_path)
    
    try:
        minio_client.remove_object(BUCKET_NAME, file_path)
    except:
        pass
    
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
