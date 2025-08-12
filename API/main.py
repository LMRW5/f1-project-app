from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import joblib
import pandas as pd
import csv
from ML.Quali_runner import predict_quali_order
from ML.Race_runner import predict_race_order

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
model_path = os.path.join("ML", "f1_qualifying_predictor.pkl")
qualifying_model = joblib.load(model_path)

@app.get("/")
async def root():
    return {"message": "F1 Prediction API is running!"}


class PredictionRequest(BaseModel):
    season: int
    round: int
    race_name: str

@app.post("/predict-Quali")
async def predictQuali(req: PredictionRequest):
    try:
        results = predict_quali_order(req.season, req.round, req.race_name, qualifying_model)
        return {"status": "ok", "predictions": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/predict-Race")
async def predictRace(req: PredictionRequest):
    try:
        results = predict_race_order(req.season, req.round, req.race_name)
        return {"status": "ok", "predictions": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/Upcoming-Races")
async def upcomingRaces(req: PredictionRequest):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "ML", "data", str(req.season), "schedule.csv")
    upcoming = []
    try:
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    race_num = int(float(row["Race"]))
                    if race_num > req.round:
                        upcoming.append({
                            "Race": race_num,
                            "Name": row["Name"]
                        })
                except ValueError:
                    # Skip invalid rows
                    continue

        # Sort by race number just in case CSV is unordered
        upcoming.sort(key=lambda r: r["Race"])

    except FileNotFoundError:
        return {"status": "error", "message": f"Schedule for {req.season} not found"}
    
    return {"status": "ok", "upcoming": upcoming}

@app.post("/Driver-Photos")
async def driverPhotos(req: PredictionRequest):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "ML", "data", str(req.season), "schedule.csv")
    pictures = []
    race = None
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == req.round:
                race = row["Name"]
    
    if not race:
        return pictures
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "ML", "data", str(req.season), f"{race} R.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["FullName"] == "Franco Colapinto":
                pictures.append({"Driver": row["FullName"],
                              "Image": "https://e2.365dm.com/f1/drivers/256x256/h_full_1563.png", 
                              "Color": row["TeamColor"],
                              "Team": row["TeamName"]})
            else:
                pictures.append({"Driver": row["FullName"],
                                "Image": row["HeadshotUrl"],
                                "Color": row["TeamColor"],
                                "Team": row["TeamName"]})
    
    return pictures
