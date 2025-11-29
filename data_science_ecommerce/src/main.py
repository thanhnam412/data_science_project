import uuid
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import redis
import json

app = FastAPI(title="File Reader API (Redis Version)", version="1.0.0")

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ===============================
# Redis Setup
# ===============================
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ===============================
# File storage directory
# ===============================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


# Save metadata to redis
def save_metadata(file_id, metadata: dict):
    redis_client.set(f"file:{file_id}", json.dumps(metadata))


# Load metadata
def load_metadata(file_id):
    value = redis_client.get(f"file:{file_id}")
    if value is None:
        return None
    return json.loads(value)


# ==========================================
# 📌 API 1 — Upload + Read CSV/XLSX
# ==========================================
@app.post("/api/read-file")
async def read_file(
    type_file: str = Form(...), file: UploadFile = File(...)  # csv hoặc xlsx
):
    # Validate type
    print(type_file)
    ext = file.filename.split(".")[-1].lower()

    if type_file not in ["csv", "xlsx"]:
        return {"error": "type_file phải là csv hoặc xlsx"}

    if ext not in ["csv", "xlsx"]:
        return {"error": "File không đúng định dạng"}

    # Create UUID
    file_id = str(uuid.uuid4())

    # Save file
    saved_path = os.path.join(DATA_DIR, f"{file_id}.{ext}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    # Read file
    if ext == "csv":
        df = pd.read_csv(saved_path)
    else:
        df = pd.read_excel(saved_path)

    # Extract info
    columns = df.columns.tolist()
    head5 = df.head(5).to_dict(orient="records")

    # Metadata
    metadata = {
        "id": file_id,
        "original_filename": file.filename,
        "saved_path": saved_path,
        "ext": ext,
    }

    # Save metadata to Redis
    save_metadata(file_id, metadata)

    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "columns": columns,
        "head5": head5,
    }


# ==========================================
# 📌 API 2 — Load file again by ID
# ==========================================
@app.get("/api/read-file/{file_id}")
def read_file_by_id(file_id: str):

    metadata = load_metadata(file_id)
    if metadata is None:
        return {"error": "file_id không tồn tại trong Redis"}

    path = metadata["saved_path"]
    ext = metadata["ext"]

    # Read file again
    if ext == "csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    return {
        "file_id": file_id,
        "original_filename": metadata["original_filename"],
        "columns": df.columns.tolist(),
        "head5": df.head(5).to_dict(orient="records"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
