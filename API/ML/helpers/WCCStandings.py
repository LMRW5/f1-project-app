import os, csv, collections, fastf1
import pandas as pd

def add_standings(season):
    SEASON = season
    totalscores = collections.defaultdict(float)

    schedule = fastf1.get_event_schedule(SEASON)
    race = 1

    with open(f"../data/{SEASON}/Team Scores.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=["Race", "TeamName", "Points", "Placement"])
        writer.writeheader()

    while True:
        try:
            gp = schedule.get_event_by_round(race)
            path = f"../data/{SEASON}/{gp['EventName']} R.csv"

            with open(path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    totalscores[row["TeamName"]] += float(row["Points"])

            # Sort teams by current total score
            sorted_teams = sorted(totalscores.items(), key=lambda x: x[1], reverse=True)

            # Write standings after this race
            with open(f"../data/{SEASON}/Team Scores.csv", "a") as f:
                writer = csv.DictWriter(f, fieldnames=["Race", "TeamName", "Points", "Placement"])
                for i, (team, points) in enumerate(sorted_teams):
                    writer.writerow({
                        "Race": race,
                        "TeamName": team,
                        "Points": points,
                        "Placement": i + 1  # Placement starts at 1
                    })

            race += 1

        except Exception:
            break

    # Final cumulative team standings
    with open(f"../data/{SEASON}/Final Team Scores.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=["TeamName", "TotalPoints"])
        writer.writeheader()
        for team, points in sorted(totalscores.items(), key=lambda x: x[1], reverse=True):
            writer.writerow({"TeamName": team, "TotalPoints": points})


