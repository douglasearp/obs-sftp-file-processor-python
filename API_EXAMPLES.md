# API Usage Examples

This document provides practical examples of using the OBS SFTP File Processor API.

## Base URL
```
http://localhost:8000
```

## Authentication
The API connects to Azure Storage SFTP using configured credentials. No additional authentication is required for the API endpoints.

## Endpoints

### 1. Health Check
```bash
# Basic health check
curl http://localhost:8000/

# Detailed health check
curl http://localhost:8000/health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "0.1.0",
    "timestamp": "2025-10-22T11:49:45.361713"
}
```

### 2. List All Files
```bash
curl http://localhost:8000/files
```

**Response:**
```json
{
    "path": ".",
    "files": [
        {
            "name": "FEDACHOUT_20251014163742.txt",
            "path": "./FEDACHOUT_20251014163742.txt",
            "size": 949,
            "modified": 1761153743.0,
            "is_directory": false,
            "permissions": "-rw-r-----"
        },
        {
            "name": "test.txt.rtf",
            "path": "./test.txt.rtf",
            "size": 377,
            "modified": 1761149315.0,
            "is_directory": false,
            "permissions": "-rw-r-----"
        }
    ],
    "total_count": 2
}
```

### 3. Get File by Exact Name
```bash
# Get a specific file by name
curl http://localhost:8000/file/FEDACHOUT_20251014163742.txt
```

**Response:**
```json
{
    "file_info": {
        "name": "FEDACHOUT_20251014163742.txt",
        "path": "FEDACHOUT_20251014163742.txt",
        "size": 949,
        "modified": 1761153743.0,
        "is_directory": false,
        "permissions": "-rw-r-----"
    },
    "content": "101021000021 12345678902510141637A094101JPMORGAN CHASE BANK...",
    "encoding": "utf-8",
    "content_type": "text/plain"
}
```

### 4. Search Files by Name Pattern
```bash
# Search for files containing "FEDACH"
curl http://localhost:8000/files/search/FEDACH

# Search for files containing "test"
curl http://localhost:8000/files/search/test
```

**Response:**
```json
{
    "path": ".",
    "files": [
        {
            "name": "FEDACHOUT_20251014163742.txt",
            "path": "./FEDACHOUT_20251014163742.txt",
            "size": 949,
            "modified": 1761153743.0,
            "is_directory": false,
            "permissions": "-rw-r-----"
        }
    ],
    "total_count": 1
}
```

### 5. Read File by Path
```bash
# Read file using full path
curl http://localhost:8000/files/test.txt.rtf
```

**Response:**
```json
{
    "file_info": {
        "name": "test.txt.rtf",
        "path": "test.txt.rtf",
        "size": 377,
        "modified": 1761149315.0,
        "is_directory": false,
        "permissions": "-rw-r-----"
    },
    "content": "{\\rtf1\\ansi\\ansicpg1252\\cocoartf2822...",
    "encoding": "utf-8",
    "content_type": "application/rtf"
}
```

## Error Handling

### File Not Found (404)
```bash
curl http://localhost:8000/file/nonexistent.txt
```

**Response:**
```json
{
    "detail": "File not found: nonexistent.txt"
}
```

### Search with No Results
```bash
curl http://localhost:8000/files/search/nonexistent
```

**Response:**
```json
{
    "path": ".",
    "files": [],
    "total_count": 0
}
```

## File Types Supported

The API automatically detects and handles various file types:

- **Text Files**: `.txt`, `.log`, `.csv`
- **Rich Text**: `.rtf`
- **Data Files**: `.json`, `.xml`
- **Binary Files**: Automatically encoded as base64
- **ACH Files**: Financial transaction files

## Content Type Detection

The API automatically detects MIME types:
- `text/plain` - Text files
- `application/rtf` - RTF files
- `application/json` - JSON files
- `application/octet-stream` - Binary files

## Encoding Support

The API supports multiple text encodings:
- **UTF-8** (default)
- **Latin-1**
- **CP1252**
- **ISO-8859-1**
- **Base64** (for binary files)

## Performance

Typical response times:
- **Health check**: ~10ms
- **File listing**: ~100ms
- **File reading**: ~50ms
- **Search operations**: ~150ms

## Interactive Documentation

Visit the interactive API documentation at:
```
http://localhost:8000/docs
```

This provides a Swagger UI interface for testing all endpoints directly in your browser.

## Python Client Example

```python
import requests

# Base URL
base_url = "http://localhost:8000"

# List all files
response = requests.get(f"{base_url}/files")
files = response.json()
print(f"Found {files['total_count']} files")

# Get a specific file
response = requests.get(f"{base_url}/file/FEDACHOUT_20251014163742.txt")
file_data = response.json()
print(f"File: {file_data['file_info']['name']}")
print(f"Size: {file_data['file_info']['size']} bytes")
print(f"Content: {file_data['content'][:100]}...")

# Search for files
response = requests.get(f"{base_url}/files/search/FEDACH")
search_results = response.json()
print(f"Found {search_results['total_count']} files matching 'FEDACH'")
```

## JavaScript Client Example

```javascript
// List all files
fetch('http://localhost:8000/files')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.total_count} files`);
    data.files.forEach(file => {
      console.log(`- ${file.name} (${file.size} bytes)`);
    });
  });

// Get specific file
fetch('http://localhost:8000/file/FEDACHOUT_20251014163742.txt')
  .then(response => response.json())
  .then(data => {
    console.log(`File: ${data.file_info.name}`);
    console.log(`Content: ${data.content.substring(0, 100)}...`);
  });
```
