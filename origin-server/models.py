from pydantic import BaseModel
from typing import List

class FileInfo(BaseModel):
    Name: str
    Hash: str
    TimeStamp: str

class ClientRequest(BaseModel):
    Type: int
    FileList: List[FileInfo]
    IP: str
    Lat: float
    Lng: float

class CDNResponse(BaseModel):
    cdn_id: int
    cdn_address: str

class SyncResponse(BaseModel):
    files: List[dict]

class ExplicitResponse(BaseModel):
    cdn_address: str
    file_name: str
