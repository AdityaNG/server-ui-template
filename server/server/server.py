import csv
import glob
import hashlib
import logging
import os
import subprocess
import zipfile
import base64
from datetime import datetime
from typing import Any, Dict, List

from bson.binary import Binary
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pymongo import MongoClient
from pymongo.database import Database

from .settings import DATA_STORAGE_PATH, MONGO_URI


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Outputs to console
        logging.FileHandler("server.log"),  # Outputs to file
    ],
)

logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
C
async def get_mongodb() -> Database:
    client: MongoClient = MongoClient(MONGO_URI)
    db: Database = client.get_default_database()
    return db


class HeartbeatResponse(BaseModel):
    status: str


@app.post("/api/heartbeat")
async def upload_data(
    db: Database = Depends(get_mongodb),
) -> HeartbeatResponse:
    try:
        # Attempt to run a simple command to check MongoDB connection
        await db.command("ping")
        logger.info("heartbeat error")
        return HeartbeatResponse(status="ok")
    except Exception as e:
        logger.error(f"MongoDB error: {e}")
        return HeartbeatResponse(status="mongo error")
    

# Mount the static files directory
os.makedirs(DATA_STORAGE_PATH, exist_ok=True)
app.mount("/data", StaticFiles(directory=DATA_STORAGE_PATH), name="data")

# Add a catch-all route for serving files from DATA_STORAGE_PATH
@app.get("/data/{file_path:path}")
async def serve_file(file_path: str):
    full_path = os.path.join(DATA_STORAGE_PATH, file_path)
    logger.info("full_path: " + str(full_path))
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")
