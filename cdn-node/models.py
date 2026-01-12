from pydantic import BaseModel

class FilePutRequest(BaseModel):
    content: str
    file_hash: str
    timestamp: str

class FileGetResponse(BaseModel):
    content: str
    source: str
