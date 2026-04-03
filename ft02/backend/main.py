from fastapi import FastAPI
from backend.api.simulate_api import router as simulate_router

app = FastAPI()

app.include_router(simulate_router)

@app.get("/")
def root():
    return {"message": "Backend running"}