from fastapi import FastAPI

from app.endpoint import router
from app import API_INFO


app = FastAPI(**API_INFO)

app.include_router(router)
