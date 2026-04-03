from fastapi import FastAPI
from api.simulate_api import router as simulate_router
from api.feature_api import router as feature_router
from api.credit_api import router as credit_router
from api.bankruptcy_api import router as bankruptcy_router
from api.fraud_api import router as fraud_router

app = FastAPI()

app.include_router(simulate_router)
app.include_router(feature_router)
app.include_router(credit_router)
app.include_router(bankruptcy_router)
app.include_router(fraud_router)

@app.get("/")
def root():
    return {"message": "Backend running"}