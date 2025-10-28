# OBS SFTP File Processor

A FastAPI application that reads files from Azure Storage SFTP server and renders their contents.

## Features

- **SFTP File Operations**: Connect to Azure Storage SFTP server and read files
- **Oracle Database Integration**: Full CRUD operations for ACH_FILES table
- **File Sync**: Automatic sync from SFTP to Oracle database
- **RESTful API**: Complete FastAPI endpoints for all operations
- **Secure Authentication**: SSH keys or passwords for SFTP
- **Comprehensive Testing**: Mock and integration tests included
- **Error Handling**: Robust error handling and logging
- **Content Detection**: Automatic content type and encoding detection

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

### SFTP Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /files` - List files in root directory
- `GET /files?path=/remote/path` - List files in specific directory
- `GET /files/{file_path}` - Read and render file contents
- `GET /files/search/{file_name}` - Search files by name pattern
- `GET /file/{file_name}` - Get specific file by exact name

### Oracle Database Endpoints
- `GET /oracle/ach-files` - List ACH_FILES records
- `POST /oracle/ach-files` - Create new ACH_FILES record
- `GET /oracle/ach-files/{id}` - Get specific ACH_FILES record
- `PUT /oracle/ach-files/{id}` - Update ACH_FILES record
- `DELETE /oracle/ach-files/{id}` - Delete ACH_FILES record
- `POST /sync/sftp-to-oracle` - Sync SFTP files to Oracle database

## Configuration

Set the following environment variables in `.env`:

### SFTP Configuration
- `SFTP_HOST` - Azure Storage SFTP hostname
- `SFTP_PORT` - SFTP port (default: 22)
- `SFTP_USERNAME` - SFTP username
- `SFTP_PASSWORD` - SFTP password (or use SSH key)
- `SFTP_KEY_PATH` - Path to SSH private key (optional)
- `SFTP_TIMEOUT` - Connection timeout in seconds

### Oracle Database Configuration
- `ORACLE_HOST` - Oracle database host
- `ORACLE_PORT` - Oracle database port (default: 1521)
- `ORACLE_SERVICE_NAME` - Oracle service name
- `ORACLE_USERNAME` - Oracle username
- `ORACLE_PASSWORD` - Oracle password
- `ORACLE_SCHEMA` - Oracle schema name

### Application Settings
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
