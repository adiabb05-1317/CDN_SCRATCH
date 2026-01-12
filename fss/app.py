from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi import Body
import httpx
import os
from storage import MinIOStorage

app = FastAPI()
storage = MinIOStorage()

META_SERVER_URL = os.getenv('META_SERVER_URL', 'http://meta-server:8002')

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/get/{file_path:path}", response_class=PlainTextResponse)
def get_file(file_path: str):
    try:
        content = storage.get_file(file_path)
        return content.decode('utf-8')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/post/{file_path:path}")
async def post_file(file_path: str, content: str = Body(..., media_type="text/plain")):
    try:
        content_bytes = content.encode('utf-8')
        storage.put_file(file_path, content_bytes)
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{META_SERVER_URL}/meta/update",
                json={
                    "file_name": file_path,
                    "file_hash": "",
                    "timestamp": "0",
                    "cdn_id": -1
                }
            )
        
        return {"status": "success", "file": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/{file_path:path}")
async def delete_file(file_path: str):
    try:
        storage.delete_file(file_path)
        
        async with httpx.AsyncClient() as client:
            await client.request(
                "DELETE",
                f"{META_SERVER_URL}/meta/delete",
                json={"file_name": file_path}
            )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list")
def list_files():
    try:
        files = storage.list_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)

