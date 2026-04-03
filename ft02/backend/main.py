from fastapi import FastAPI
from backend.api.simulate_api import router as simulate_router
from backend.api.feature_api import router as feature_router
from backend.api.credit_api import router as credit_router
from backend.api.bankruptcy_api import router as bankruptcy_router
from backend.api.fraud_api import router as fraud_router

app = FastAPI()

app.include_router(simulate_router)
app.include_router(feature_router)
app.include_router(credit_router)
app.include_router(bankruptcy_router)
app.include_router(fraud_router)

@app.get("/")
def root():
    return {"message": "Backend running"}