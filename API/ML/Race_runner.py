# predict_model.py

import joblib
import pandas as pd
import numpy as np
import os
from .model import build_winrate_feature_vector, flatten_features, driversANDteams


def predict_with_confidence(model, X_input):
    pd.set_option('future.no_silent_downcasting', True)
    # Get predictions from all trees
    X_array = X_input.values  # Strip column names to avoid warning
    tree_preds = np.array([tree.predict(X_array)[0] for tree in model.estimators_])
    mean_prediction = np.mean(tree_preds)
    std_dev = np.std(tree_preds)

    # Soft normalization for confidence: lower std = higher confidence
    confidence = 1 - (std_dev / (std_dev + 1))  # bounded in (0, 1)
    return mean_prediction, confidence, std_dev

def predict_race_order(season, round_number, race_name):
    # Load trained model
    model_path = os.path.join(os.path.dirname(__file__), "f1_position_predictor.pkl")
    model = joblib.load(model_path)

    # Collect drivers and teams for the race
    drivers, teams = driversANDteams(season, round_number)

    predictions = []

    for driver in drivers:
        try:
            features = build_winrate_feature_vector(driver, teams[driver], season, race_name, round_number)
            flat_features = flatten_features(features)
            X_input = pd.DataFrame([flat_features]).infer_objects(copy=False).fillna(0)

            score, confidence, std = predict_with_confidence(model, X_input)
            predictions.append((driver, score, confidence, std))
        except Exception as e:
            print(f"Error predicting for {driver}: {e}")

    # Sort drivers by predicted score (lower = better position)
    predictions.sort(key=lambda x: x[1])

    #Return Value
    rval = []

    # Display prediction
    print(f"\n📊 Predicted finishing order for {race_name} {season} (Using data from R{round_number}):\n")
    for idx, (driver, score, confidence, std) in enumerate(predictions, 1):
        print(f"{idx:2d}. {driver:25} Score: {score:.3f} | Std Dev: {std:.3f} | Confidence: {confidence:.2f}")
        rval.append({"Driver": driver, "Values":{"Pos":idx, "Score": score, "Std Dev": std, "Confidence": confidence}})

    return rval

if __name__ == "__main__":
    predict_race_order(2025, 14, "Dutch Grand Prix") # Predict the order for the 2025 dutch gp using data up to r14
 