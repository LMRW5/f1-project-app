from model import *
from Quali_runner import *
import csv
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

def train_model():
    dataset = []
    model = joblib.load("f1_qualifying_predictor.pkl")


    for season in range(2020, 2025):  # Training up to 2024
        with open(f"data/{season}/schedule.csv", "r") as schedule_file:
            schedule_reader = csv.DictReader(schedule_file)
            for row in schedule_reader:
                round_num = int(row["Race"])

                race = row["Name"]
                order = predict_quali_order(season, round_num, race, model)

                try:
                    with open(f"data/{season}/{race} R.csv", "r") as result_file:
                        result_reader = csv.DictReader(result_file)
                        for row in result_reader:
                            driver = row["FullName"]
                            team = row["TeamName"]
                            try:
                                winrate = build_winrate_feature_vector(driver, team, season, race, round_num)
                                for r in order:
                                    if r["Driver"] == driver:
                                        winrate["Qualifying_Predictions"] = r["Values"]
                                features = flatten_features(winrate)
                                target_position = int(get_race_results(driver, season, race))
                                features["FinalPosition"] = target_position
                                dataset.append(features)
                            except Exception as e:
                                print(f"[TRAIN] Error with {driver} at {season} {race}: {e}")
                except FileNotFoundError:
                    continue


    # DataFrame
    df = pd.DataFrame(dataset).fillna(0)
    X = df.drop(columns=["FinalPosition"])
    y = df["FinalPosition"]

    # Split into train/test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestRegressor(
    n_estimators=150,
    max_depth=6,
    min_samples_leaf=3,
    min_samples_split=5,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    print("📊 Training Set R²:", r2_score(y_train, y_train_pred))
    print("📉 Training MSE:", mean_squared_error(y_train, y_train_pred))
    print("🧪 Test Set R²:", r2_score(y_test, y_test_pred))
    print("🧪 Test MSE:", mean_squared_error(y_test, y_test_pred))

    print("Weights: \n")
    importances = model.feature_importances_
    for name, importance in sorted(zip(X.columns, importances), key=lambda x: -x[1]):
        print(f"{name:30}: {importance:.4f}")

    # Save model
    joblib.dump(model, "f1_position_predictor.pkl")
    print("✅ Model saved as f1_position_predictor.pkl")




if __name__ == "__main__":
    train_model()
