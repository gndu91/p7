import pandas as pd
from fastapi import FastAPI, HTTPException

from model import ClientDataModel, model_pipeline, BUSINESS_THRESHOLD

app = FastAPI(
    title="Credit Scoring API",
    description="Accept or decline a credit based on probabilities of non payment.",
    version="1.1.0"
)

@app.get("/status", tags=["Health Check"])
@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "up" if model_pipeline else "down"}

@app.post("/predict", tags=["Prediction"])
async def predict(client_data: ClientDataModel):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Unavailable model")
    client_df = pd.DataFrame([client_data.model_dump()])
    try:
        probability = model_pipeline.predict_proba(client_df)[0][1]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error occured during prediction : {e}")
    return {
        "client_id": client_data.SK_ID_CURR,
        "probability_default": round(float(probability), 4),
        "decision": "yes" if probability < BUSINESS_THRESHOLD else "no",
        "threshold": BUSINESS_THRESHOLD
    }