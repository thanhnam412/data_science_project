from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.mvc.schema import BaseModel

app = FastAPI(default_response_class=JSONResponse)


@app.get("/")
def read_root():
    return {"Hello": "World"}
