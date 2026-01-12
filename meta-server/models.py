from pydantic import BaseModel
from typing import List, Optional

class Address(BaseModel):
    ipAddr: str
    latLng: List[float]

class FileInfo(BaseModel):
    Name: str
    Hash: str
    TimeStamp: str

class CDNRegisterRequest(BaseModel):
    Type: int
    IP: str
    Lat: float
    Lng: float

class CDNRegisterResponse(BaseModel):
    cdn_id: int

class FileUpdateRequest(BaseModel):
    file_name: str
    file_hash: str
    timestamp: str
    cdn_id: int

class FileQueryRequest(BaseModel):
    file_name: str
    client_lat: float
    client_lng: float

class FileQueryResponse(BaseModel):
    cdn_id: int
    cdn_address: str

class DeleteFileRequest(BaseModel):
    file_name: str
