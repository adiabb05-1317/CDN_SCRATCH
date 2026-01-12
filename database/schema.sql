CREATE TABLE IF NOT EXISTS cdn_nodes (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS files (
    name TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cdn_file_mappings (
    id SERIAL PRIMARY KEY,
    file_name TEXT REFERENCES files(name) ON DELETE CASCADE,
    cdn_id INTEGER REFERENCES cdn_nodes(id) ON DELETE CASCADE,
    cached_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(file_name, cdn_id)
);

CREATE TABLE IF NOT EXISTS file_timestamps (
    file_name TEXT PRIMARY KEY REFERENCES files(name) ON DELETE CASCADE,
    timestamp BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cdn_file_mappings_file ON cdn_file_mappings(file_name);
CREATE INDEX IF NOT EXISTS idx_cdn_file_mappings_cdn ON cdn_file_mappings(cdn_id);
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
