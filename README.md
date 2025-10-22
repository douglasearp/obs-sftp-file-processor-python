# OBS SFTP File Processor

A FastAPI application that reads files from Azure Storage SFTP server and renders their contents.

## Features

- Connect to Azure Storage SFTP server
- Read files from remote SFTP location
- Render file contents via REST API
- Secure authentication with SSH keys or passwords
- Comprehensive error handling and logging
- Automatic content type detection
- Support for various text encodings

## Setup

1. Create virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv add fastapi uvicorn paramiko pydantic python-dotenv loguru
   ```

3. Configure environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your SFTP credentials
   ```

4. Run the application:
   ```bash
   # Using UV
   uv run python main.py
   
   # Or directly with uvicorn
   uv run uvicorn src.obs_sftp_file_processor.main:app --reload
   ```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /files` - List files in root directory
- `GET /files?path=/remote/path` - List files in specific directory
- `GET /files/{file_path}` - Read and render file contents

## Configuration

Set the following environment variables in `.env`:

- `SFTP_HOST` - Azure Storage SFTP hostname
- `SFTP_PORT` - SFTP port (default: 22)
- `SFTP_USERNAME` - SFTP username
- `SFTP_PASSWORD` - SFTP password (or use SSH key)
- `SFTP_KEY_PATH` - Path to SSH private key (optional)
- `APP_DEBUG` - Enable debug mode (default: false)
- `APP_LOG_LEVEL` - Logging level (default: INFO)

## Usage Examples

### List files in root directory
```bash
curl http://localhost:8000/files
```

### List files in specific directory
```bash
curl "http://localhost:8000/files?path=/data/uploads"
```

### Read a specific file
```bash
curl http://localhost:8000/files/data/sample.txt
```

### Health check
```bash
curl http://localhost:8000/health
```

## Response Format

### File Content Response
```json
{
  "file_info": {
    "name": "sample.txt",
    "path": "/data/sample.txt",
    "size": 1024,
    "modified": 1640995200.0,
    "is_directory": false,
    "permissions": "-rw-r--r--"
  },
  "content": "File content here...",
  "encoding": "utf-8",
  "content_type": "text/plain"
}
```

### File List Response
```json
{
  "path": "/data",
  "files": [
    {
      "name": "file1.txt",
      "path": "/data/file1.txt",
      "size": 1024,
      "modified": 1640995200.0,
      "is_directory": false,
      "permissions": "-rw-r--r--"
    }
  ],
  "total_count": 1
}
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (e.g., trying to read a directory)
- `404` - File not found
- `500` - Internal server error

## Development

### Project Structure
```
src/obs_sftp_file_processor/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models.py            # Pydantic models
└── sftp_service.py      # SFTP operations
```

### Running Tests
```bash
uv add --dev pytest pytest-asyncio
uv run pytest
```

### Code Formatting
```bash
uv add --dev black ruff
uv run black src/
uv run ruff check src/
```
