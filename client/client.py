import httpx
import hashlib
import os
import time
from pathlib import Path
from typing import List, Dict
import asyncio
import argparse

class CDNClient:
    def __init__(self, origin_url: str, client_lat: float, client_lng: float):
        self.origin_url = origin_url
        self.client_lat = client_lat
        self.client_lng = client_lng
        self.client_ip = "127.0.0.1"
    
    def calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def scan_directory(self, directory: str) -> List[Dict]:
        files = []
        path = Path(directory)
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(path)
                file_hash = self.calculate_file_hash(str(file_path))
                timestamp = str(int(os.path.getmtime(str(file_path))))
                
                files.append({
                    "Name": str(relative_path),
                    "Hash": file_hash,
                    "TimeStamp": timestamp,
                    "FullPath": str(file_path)
                })
        
        return files
    
    async def sync_directory(self, directory: str):
        print(f"Scanning directory: {directory}")
        files = self.scan_directory(directory)
        
        if not files:
            print("No files found in directory")
            return
        
        print(f"Found {len(files)} files")
        
        request_payload = {
            "Type": 0,
            "FileList": [{"Name": f["Name"], "Hash": f["Hash"], "TimeStamp": f["TimeStamp"]} for f in files],
            "IP": self.client_ip,
            "Lat": self.client_lat,
            "Lng": self.client_lng
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.origin_url}/origin/sync", json=request_payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nReceived CDN addresses for {len(result['files'])} files")
                
                for file_info in result['files']:
                    file_name = file_info['file_name']
                    cdn_address = file_info['cdn_address']
                    cdn_id = file_info.get('cdn_id', -1)
                    
                    matching_file = next((f for f in files if f['Name'] == file_name), None)
                    if matching_file:
                        if cdn_id == -1:
                            # Upload to FSS
                            await self.upload_file_to_fss(
                                matching_file['FullPath'],
                                file_name,
                                cdn_address
                            )
                        else:
                            # Upload to CDN
                            await self.upload_file_to_cdn(
                                matching_file['FullPath'],
                                file_name,
                                matching_file['Hash'],
                                matching_file['TimeStamp'],
                                cdn_address
                            )
            else:
                print(f"Error: {response.status_code} - {response.text}")

    async def upload_file_to_fss(self, file_path: str, file_name: str, fss_address: str):
        with open(file_path, 'r') as f:
            content = f.read()
        
        fss_url = f"http://{fss_address}/post/{file_name}"
        
        headers = {"Content-Type": "text/plain"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(fss_url, content=content, headers=headers)
                if response.status_code == 200:

                    print(f"✓ Uploaded to FSS: {file_name}")
                else:
                    print(f"✗ Failed to upload to FSS {file_name}: {response.status_code}")
            except Exception as e:
                print(f"✗ Error uploading to FSS {file_name}: {str(e)}")
    
    async def upload_file_to_cdn(self, file_path: str, file_name: str, file_hash: str, timestamp: str, cdn_address: str):

        with open(file_path, 'r') as f:
            content = f.read()
        
        cdn_url = f"http://{cdn_address}/cdn/cache/{file_name}"
        
        payload = {
            "content": content,
            "file_hash": file_hash,
            "timestamp": timestamp
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(cdn_url, json=payload)
                if response.status_code == 200:
                    print(f"✓ Uploaded: {file_name} to {cdn_address}")
                else:
                    print(f"✗ Failed to upload {file_name}: {response.status_code}")
            except Exception as e:
                print(f"✗ Error uploading {file_name}: {str(e)}")
    
    async def get_file_explicit(self, file_name: str):
        request_payload = {
            "Type": 1,
            "FileList": [{"Name": file_name, "Hash": "", "TimeStamp": "0"}],
            "IP": self.client_ip,
            "Lat": self.client_lat,
            "Lng": self.client_lng
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.origin_url}/origin/explicit", json=request_payload)
            
            if response.status_code == 200:
                result = response.json()
                cdn_address = result['cdn_address']
                cdn_id = result.get('cdn_id', -1)
                
                print(f"Fetching {file_name} from {cdn_address} (ID: {cdn_id})")
                
                if cdn_id == -1:
                    cdn_url = f"http://{cdn_address}/get/{file_name}"
                else:
                    cdn_url = f"http://{cdn_address}/cdn/cache/{file_name}"
                
                file_response = await client.get(cdn_url)

                
                if file_response.status_code == 200:
                    print(f"\nFile content:\n{file_response.text}")
                    return file_response.text
                else:
                    print(f"Error fetching file: {file_response.status_code}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

async def main():
    parser = argparse.ArgumentParser(description='CDN Client')
    parser.add_argument('command', choices=['sync', 'get'], help='Command to execute')
    parser.add_argument('path', help='Directory path for sync or file name for get')
    parser.add_argument('--origin', default='http://localhost:8001', help='Origin server URL')
    parser.add_argument('--lat', type=float, default=37.7749, help='Client latitude')
    parser.add_argument('--lng', type=float, default=-122.4194, help='Client longitude')
    
    args = parser.parse_args()
    
    client = CDNClient(args.origin, args.lat, args.lng)
    
    if args.command == 'sync':
        await client.sync_directory(args.path)
    elif args.command == 'get':
        await client.get_file_explicit(args.path)

if __name__ == "__main__":
    asyncio.run(main())
