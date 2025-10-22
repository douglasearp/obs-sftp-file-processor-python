"""Entry point for the FastAPI application."""

import uvicorn
from src.obs_sftp_file_processor.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.obs_sftp_file_processor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
