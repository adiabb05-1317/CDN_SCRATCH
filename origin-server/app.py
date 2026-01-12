from fastapi import FastAPI, HTTPException
import httpx
import os
from models import ClientRequest, SyncResponse, ExplicitResponse

app = FastAPI()

META_SERVER_URL = os.getenv('META_SERVER_URL', 'http://meta-server:8002')

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/origin/sync")
async def handle_sync(request: ClientRequest):
    results = []
    
    async with httpx.AsyncClient() as client:
        for file_info in request.FileList:
            query_payload = {
                "file_name": file_info.Name,
                "client_lat": request.Lat,
                "client_lng": request.Lng
            }
            
            response = await client.post(f"{META_SERVER_URL}/meta/query", json=query_payload)
            
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "file_name": file_info.Name,
                    "cdn_address": data["cdn_address"],
                    "cdn_id": data["cdn_id"]
                })
    
    return {"files": results}

@app.post("/origin/explicit")
async def handle_explicit(request: ClientRequest):
    if not request.FileList:
        raise HTTPException(status_code=400, detail="No files specified")
    
    file_info = request.FileList[0]
    
    async with httpx.AsyncClient() as client:
        query_payload = {
            "file_name": file_info.Name,
            "client_lat": request.Lat,
            "client_lng": request.Lng
        }
        
        response = await client.post(f"{META_SERVER_URL}/meta/query", json=query_payload)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "cdn_address": data["cdn_address"],
                "file_name": file_info.Name,
                "cdn_id": data["cdn_id"]
            }

        else:
            raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
