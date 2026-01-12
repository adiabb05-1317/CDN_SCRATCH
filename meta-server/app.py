from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import math
from typing import List, Tuple
import os
from models import (
    CDNRegisterRequest, CDNRegisterResponse,
    FileUpdateRequest, FileQueryRequest, FileQueryResponse,
    DeleteFileRequest
)
from database import Database

app = FastAPI()
db = Database()

FSS_LAT = 34.05
FSS_LNG = -118.44

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def get_closest_cdn(cdn_ids: List[int], client_lat: float, client_lng: float) -> int:
    if not cdn_ids:
        return -1
    
    min_distance = float('inf')
    closest_cdn = -1
    
    for cdn_id in cdn_ids:
        cdn = db.get_cdn_by_id(cdn_id)
        if cdn:
            distance = calculate_distance(cdn['lat'], cdn['lng'], client_lat, client_lng)
            if distance < min_distance:
                min_distance = distance
                closest_cdn = cdn_id
    
    return closest_cdn

def is_cdn_closer_than_fss(cdn_id: int, client_lat: float, client_lng: float) -> bool:
    cdn = db.get_cdn_by_id(cdn_id)
    if not cdn:
        return False
    
    dist_to_cdn = calculate_distance(cdn['lat'], cdn['lng'], client_lat, client_lng)
    dist_to_fss = calculate_distance(FSS_LAT, FSS_LNG, client_lat, client_lng)
    
    return dist_to_cdn <= dist_to_fss

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/meta/register", response_model=CDNRegisterResponse)
def register_cdn(request: CDNRegisterRequest):
    cdn_id = db.register_cdn(request.IP, request.Lat, request.Lng)
    return CDNRegisterResponse(cdn_id=cdn_id)

@app.post("/meta/update")
def update_file_metadata(request: FileUpdateRequest):
    db.add_or_update_file(request.file_name, request.file_hash, int(request.timestamp))
    db.add_cdn_file_mapping(request.file_name, request.cdn_id)
    return {"status": "success"}

@app.post("/meta/query", response_model=FileQueryResponse)
def query_file_location(request: FileQueryRequest):
    cdns_with_file = db.get_cdns_with_file(request.file_name)
    
    if cdns_with_file:
        closest_cdn = get_closest_cdn(cdns_with_file, request.client_lat, request.client_lng)
        if closest_cdn != -1:
            if is_cdn_closer_than_fss(closest_cdn, request.client_lat, request.client_lng):
                cdn = db.get_cdn_by_id(closest_cdn)
                return FileQueryResponse(cdn_id=closest_cdn, cdn_address=cdn['address'])
    
    return FileQueryResponse(cdn_id=-1, cdn_address=f"localhost:5050")


@app.delete("/meta/delete")
def delete_file(request: DeleteFileRequest):
    db.delete_file(request.file_name)
    return {"status": "success"}

@app.get("/meta/cdns")
def get_all_cdns():
    return {"cdns": db.get_all_cdns()}

@app.get("/meta/files")
def get_all_files():
    cursor = db.get_cursor()
    cursor.execute("SELECT * FROM files")
    files = cursor.fetchall()
    cursor.close()
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
