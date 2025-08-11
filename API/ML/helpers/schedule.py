import os, csv, fastf1

def main():
    for season in range(2025,2026):
        path = f"../data/{season}/schedule.csv"
        with open(path, "w") as file:
            writer = csv.DictWriter(file, fieldnames=["Race", "Name"])
            writer.writeheader()
            race = 1
            while True:
                try:
                    event = fastf1.get_event(season,race)
                    writer.writerow({"Race": event["RoundNumber"], "Name": event["EventName"]})
                    race += 1
                except Exception:
                    break

if __name__ == "__main__":
    main()
