import fastf1
import os, csv

def main():
    for season in range(2025,2026):
        with open(f"../data/{season}/rain.csv", "w") as file:
            writer = csv.DictWriter(file, fieldnames=["Round","Race","Rain"])
            writer.writeheader()
        rounds = 1
        while True:
            try:
                session = fastf1.get_session(season, rounds, "R")
                session.load()

                rained = session.weather_data["Rainfall"].any()

                with open(f"../data/{season}/rain.csv", "a") as file:
                    writer = csv.DictWriter(file, fieldnames=["Round","Race","Rain"])
                    writer.writerow({"Round": rounds, "Race": session.event["EventName"], "Rain" : rained})
                print(f"Saved round {rounds} of {season}")
                rounds += 1

            except Exception:
                break

def add_rain(season):
    with open(f"../data/{season}/rain.csv", "w") as file:
        writer = csv.DictWriter(file, fieldnames=["Round","Race","Rain"])
        writer.writeheader()
    rounds = 1
    while True:
        try:
            session = fastf1.get_session(season, rounds, "R")
            session.load()

            rained = session.weather_data["Rainfall"].any()

            with open(f"../data/{season}/rain.csv", "a") as file:
                writer = csv.DictWriter(file, fieldnames=["Round","Race","Rain"])
                writer.writerow({"Round": rounds, "Race": session.event["EventName"], "Rain" : rained})
            print(f"Saved round {rounds} of {season}")
            rounds += 1

        except Exception:
            break

if __name__ == "__main__":
    main()
