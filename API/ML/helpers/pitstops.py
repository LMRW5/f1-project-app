from fastf1.ergast import Ergast
import pandas as pd
import os, csv


def add_pitstops(season):
    ergast = Ergast(result_type='pandas', auto_cast=True)

    # Mapping constructorName → TeamName (as used in your original dataset)
    constructor_to_teamname = {
        "McLaren": "McLaren",
        "Red Bull": "Red Bull Racing",
        "Ferrari": "Ferrari",
        "Mercedes": "Mercedes",
        "Williams": "Williams",
        "RB F1 Team": "Racing Bulls",
        "Haas F1 Team": "Haas F1 Team",
        "Sauber": "Kick Sauber",
        "Aston Martin": "Aston Martin",
        "Alpine F1 Team": "Alpine"
    }

    # Output directory
    season_dir = f"../data/{season}"
    os.makedirs(season_dir, exist_ok=True)

    # Output CSV file
    output_file = f"{season_dir}/pitstops.csv"

    # Create CSV with header (without Season)
    with open(output_file, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Round", "Team", "AveragePitStop"])
        writer.writeheader()

    rnd = 1
    while True:
        try:
            # Get pit stops
            pit_resp = ergast.get_pit_stops(season=season, round=rnd)
            df_pit = pd.concat(pit_resp.content, ignore_index=True)

            # Ensure duration is numeric, then convert from ns to seconds
            df_pit['duration'] = pd.to_numeric(df_pit['duration'], errors='coerce') / 1e9
            df_pit = df_pit.dropna(subset=['duration'])

            # Get race results to map drivers to teams
            results = ergast.get_race_results(season=season, round=rnd)
            df_results = results.content[0]
            driver_to_constructor = dict(zip(df_results['driverId'], df_results['constructorName']))

            # Map constructorName to original dataset's TeamName
            driver_to_teamname = {driver: constructor_to_teamname.get(constructor, constructor)
                                  for driver, constructor in driver_to_constructor.items()}
            df_pit['team'] = df_pit['driverId'].map(driver_to_teamname)

            # Group by team and calculate average pit stop in seconds
            team_avg = df_pit.groupby('team')['duration'].mean().round(2).reset_index()
            team_avg['Round'] = rnd

            # Reorder and rename columns
            team_avg['duration'] = team_avg['duration'] / 10
            team_avg = team_avg[['Round', 'team', 'duration']]
            team_avg.columns = ['Round', 'Team', 'AveragePitStop']

            # Append to CSV
            team_avg = team_avg.sort_values(by='AveragePitStop', ascending=True)
            team_avg.to_csv(output_file, mode='a', index=False, header=False)

            print(f"Saved round {rnd} of {season}")
            rnd += 1
        except Exception:
            break


