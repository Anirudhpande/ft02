from fastapi import FastAPI
from api.simulate_api import router as simulate_router

app = FastAPI(
    title="MSME Risk Intelligence API"
)

app.include_router(simulate_router)

@app.get("/")
def root():
    return {"message": "Backend running"}