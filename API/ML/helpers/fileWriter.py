import fastf1
import csv
import os

def main():
    keyValues = ["R"]

    for value in keyValues:
        for season in range(2025,2026):
            rounds = 12
            while True:
                try:
                    session = fastf1.get_session(season,rounds,value)
                    session.load()
                    path = os.path.join(f"../data/{season}", f"{session.event['EventName']} {value}.csv")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as file:
                        writer = csv.DictWriter(file, fieldnames=session.results.columns.tolist())
                        writer.writeheader()
                        for _, row in session.results.iterrows():
                            writer.writerow(row.to_dict())
                    rounds += 1
                except Exception:
                    break

def add_race(season, latest):
    session = fastf1.get_session(season,latest,"R")
    session.load()
    path = os.path.join(f"../data/{season}", f"{session.event['EventName']} R.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        writer = csv.DictWriter(file, fieldnames=session.results.columns.tolist())
        writer.writeheader()
        for _, row in session.results.iterrows():
            writer.writerow(row.to_dict())

if __name__ == "__main__":
    main()
