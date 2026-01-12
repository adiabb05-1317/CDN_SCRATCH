# Distributed CDN System

A complete Content Delivery Network implementation using Python, FastAPI, Docker, PostgreSQL, Redis, and MinIO.
<img width="515" height="497" alt="Screenshot 2026-01-12 at 11 53 02 PM" src="https://github.com/user-attachments/assets/59cfa346-87e9-4779-ba7f-990314db04dd" />


## Architecture

The system consists of 5 core components running in Docker containers:

1. **Meta Server** - System intelligence and metadata management
2. **Origin Server** - Stateless gateway for client requests
3. **CDN Node** - Edge cache with dual-layer caching (Redis + local)
4. **File Storage Server (FSS)** - Persistent storage using MinIO
5. **Client** - CLI tool for file synchronization

### Infrastructure Components

- **PostgreSQL** - Metadata storage (CDN nodes, files, mappings)
- **Redis** - Distributed cache with LRU eviction
- **MinIO** - Object storage for files

## Features

- Geographic CDN selection based on distance calculations
- Dual-layer caching (Redis primary, local LRU fallback)
- Automatic cache warming and backfill
- File synchronization with directory scanning
- Explicit file retrieval
- Horizontal scalability with Docker

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Setup

1. Clone the repository and navigate to the project directory:

```bash
cd CDN_SCRATCH
```

2. Start all services:

```bash
docker-compose up -d
```

3. Verify services are running:

```bash
docker-compose ps
```

All services should show as "healthy".

### Service Endpoints

- **Origin Server**: http://localhost:8001
- **Meta Server**: http://localhost:8002
- **CDN Node**: http://localhost:4000
- **FSS**: http://localhost:5050
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **MinIO Console**: http://localhost:9001

## Usage

### Client Installation

```bash
cd client
pip install -r requirements.txt
```

### Sync Directory

Upload all files from a directory to the CDN:

```bash
python client.py sync /path/to/directory --origin http://localhost:8001 --lat 37.7749 --lng -122.4194
```

### Get Single File

Retrieve a specific file:

```bash
python client.py get filename.txt --origin http://localhost:8001 --lat 37.7749 --lng -122.4194
```

## API Endpoints

### Origin Server

**POST /origin/sync**
- Synchronize multiple files
- Returns CDN addresses for each file

**POST /origin/explicit**
- Get single file location
- Returns CDN address for the file

### Meta Server

**POST /meta/register**
- Register a new CDN node
- Returns CDN ID

**POST /meta/query**
- Query file location
- Returns closest CDN address

**POST /meta/update**
- Update file metadata
- Tracks file-to-CDN mappings

### CDN Node

**GET /cdn/cache/{file_path}**
- Retrieve file from cache or FSS
- Implements dual-layer caching

**PUT /cdn/cache/{file_path}**
- Upload file to CDN
- Updates both cache layers

### File Storage Server

**GET /get/{file_path}**
- Retrieve file from MinIO

**POST /post/{file_path}**
- Upload file to MinIO

## CDN Selection Algorithm

The system uses a three-tier selection strategy:

1. **Find CDNs with the file** - Query metadata for CDNs that have cached the file
2. **Select closest CDN** - Calculate geographic distance using Haversine formula
3. **Compare with FSS** - If CDN is farther than FSS, return FSS address

## Database Schema

### cdn_nodes
- Stores CDN registration information
- Geographic coordinates for distance calculations

### files
- File metadata (name, hash, timestamp)

### cdn_file_mappings
- Tracks which files are cached on which CDNs

### file_timestamps
- File versioning information

## Development

### View Logs

```bash
docker-compose logs -f [service-name]
```

### Restart Service

```bash
docker-compose restart [service-name]
```

### Stop All Services

```bash
docker-compose down
```

### Clean Everything

```bash
docker-compose down -v
```

## Testing

### Test Meta Server

```bash
curl http://localhost:8002/health
curl http://localhost:8002/meta/cdns
curl http://localhost:8002/meta/files
```

### Test CDN Registration

```bash
curl -X POST http://localhost:8002/meta/register \
  -H "Content-Type: application/json" \
  -d '{"Type": 0, "IP": "localhost:4000", "Lat": 37.7749, "Lng": -122.4194}'
```

### Test File Upload

```bash
curl -X POST http://localhost:5050/post/test.txt \
  -H "Content-Type: text/plain" \
  -d "Hello, CDN!"
```

### Test File Retrieval

```bash
curl http://localhost:5050/get/test.txt
```

## Configuration

Environment variables can be configured in `docker-compose.yml`:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST` - Redis server host
- `MINIO_ENDPOINT` - MinIO server endpoint
- `META_SERVER_URL` - Meta server URL
- `CDN_LAT`, `CDN_LNG` - CDN geographic coordinates

## Architecture Diagram

```
Client
  |
  v
Origin Server (8001)
  |
  v
Meta Server (8002) <-> PostgreSQL
  |
  v
CDN Node (4000) <-> Redis <-> FSS (5050) <-> MinIO
```

## Performance

- **Redis Cache**: 512MB with LRU eviction
- **Local Cache**: 10MB per CDN node
- **Geographic Optimization**: Haversine distance calculation
- **Automatic Backfill**: Local cache to Redis on hit

## License

MIT
