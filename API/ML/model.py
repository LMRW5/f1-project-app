import csv
import os
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import joblib
import glob

def shift_recency_positions(recency_positions, n_ahead, Avg):
    # recency_positions = [Past1, Past2, Past3] (most recent first)
    # Shift the positions so that for each step ahead,
    # the most recent data (Past1) becomes None, and others move forward.
    
    shifted = recency_positions.copy()
    
    for _ in range(n_ahead):
        shifted = [Avg] + shifted[:-1]  # Insert None at Past1, drop oldest
    
    return shifted

def is_team_equivalent(current_team, historical_team):
    TEAM_NAME_ALIASES = {
    "Aston Martin": ["Aston Martin", "Racing Point"],
    "Racing Bulls": ["AlphaTauri", "Racing Bulls", "RB"],
    "RB": ["AlphaTauri", "RB"],
    "AlphaTauri": ["AlphaTauri",],
    "Kick Sauber": ["Kick Sauber", "Alfa Romeo Racing", "Alfa Romeo"],
    "Alfa Romeo": ["Alfa Romeo Racing", "Alfa Romeo"],
    "Alfa Romeo Racing": ["Alfa Romeo Racing"],
    "Mercedes": ["Mercedes"],
    "Ferrari": ["Ferrari"],
    "McLaren": ["McLaren"],
    "Red Bull Racing": ["Red Bull", "Red Bull Racing"],
    "Haas F1 Team": ["Haas", "Haas F1 Team"],
    "Williams": ["Williams"],
    "Alpine": ["Alpine", "Renault"],
    "Renault": ["Renault"],
    }
    for canonical, aliases in TEAM_NAME_ALIASES.items():
        if current_team == canonical and historical_team in aliases:
            return True
    return current_team == historical_team

def get_round_from_race_name(season, race_name):
    import csv, os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schedule_path = os.path.join(base_dir, "data", str(season), "schedule.csv")
    
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Name"].strip().lower() == race_name.strip().lower():
                return int(row["Race"])
    return None  # if race name not found

def build_winrate_feature_vector(imp_driver, imp_team, imp_season, imp_track, imp_latest_round) -> dict:
    # Baseline Data

    TRACK = imp_track
    SEASON = imp_season
    LATEST_ROUND = imp_latest_round
    DRIVER = imp_driver
    TEAM = imp_team
    # structure for model to follow and figure weights
    carFeatures = {
        "Season Avg Finish" : None,
        "Season Avg Start": None,
        "Team Constructors Championship Placement": None,
        "Team Constructors Points": None,
        "Luck Factor": {"Avg Gain": None, "Avg Luck":None, "Std Dev": None},
        "Recency Finish Bias": {"Past1": None, "Past2": None, "Past3": None},
        "Recency Start Bias": {"Past1": None, "Past2": None, "Past3": None},
    }
    teamFeatures = {
        "Average Pitstop Time": {"This Season": None, "Past on Track": None},
        "Reliability":{"DNF rate": None, "DNS rate": None},
    }
    driverFeatures = {
        "Driver Past Placements": {"Avg": None, "Car Used": None, "Teammate Gap": None, "Starting Pos": None, "Std Dev": None, "Experience": None},
        "Teammate Gap" : None,
        "Wet Weather Multiplier": {"This Season": None, "Prev Seasons": None,},

        }

    winrate = {
        "Car": carFeatures,
        "Team": teamFeatures,
        "Driver": driverFeatures
        }

    #Load data for MDOEL
    # Load average finish for driver this season
    rounds = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), f"schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) <= LATEST_ROUND:
                rounds.append(row["Name"])

    finish_sum = 0
    race_count = 0

    for round_name in rounds:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{round_name} R.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == DRIVER:
                    try:
                        pos = int(float(row["Position"]))
                        finish_sum += pos
                        race_count += 1
                    except Exception:
                        break  # skip non-finishers or invalid data

    carFeatures["Season Avg Finish"] = finish_sum / race_count if race_count > 0 else 0
    # Example: number of races ahead you want to predict (0 for current race)
    round = get_round_from_race_name(season=SEASON, race_name=TRACK)
    n_ahead = round - LATEST_ROUND -1

        # Load average start for driver this season
    rounds = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) <= LATEST_ROUND:
                rounds.append(row["Name"])

    finish_sum = 0
    race_count = 0

    for round_name in rounds:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{round_name} R.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == DRIVER:
                    try:
                        pos = int(float(row["GridPosition"]))
                        finish_sum += pos
                        race_count += 1
                    except Exception:
                        break  # skip non-finishers or invalid data

    carFeatures["Season Avg Start"] = finish_sum / race_count if race_count > 0 else 0

    # Load Recency bias for starting positions:
    recency_positions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        past_races = [row["Name"] for row in reader if int(row["Race"]) <= LATEST_ROUND]

    last_races = past_races[-3:]  # last 3 races before the current round
    last_races_reversed = list(reversed(last_races))  # most recent first

    for race in last_races_reversed:
        try:
            race_path = os.path.join(base_dir, "data", str(SEASON), f"{race} R.csv")
            with open(race_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["FullName"] == DRIVER:
                        pos = int(float(row["GridPosition"]))
                        recency_positions.append(pos)
                        break
        except Exception:
            recency_positions.append(None)

    # Make sure we have exactly 3 elements (fill with None if less)
    while len(recency_positions) < 3:
        recency_positions.append(None)

    # Shift recency positions for future races ahead
    shifted_positions = shift_recency_positions(recency_positions, n_ahead, carFeatures["Season Avg Start"])

    # Assign recency values (Past1 = most recent, Past2 = second most, etc.)
    for i in range(3):
        key = f"Past{i+1}"
        carFeatures["Recency Start Bias"][key] = shifted_positions[i]

    #Load past avg std dev from starting pos
    placements = 0
    races = 0
    for season in range(2020,SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            schedule_path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")
            if not os.path.exists(schedule_path):
                continue
            with open(schedule_path, "r") as file:
                reader = csv.DictReader(file)
                races += 1
                for row in reader:
                    if row["FullName"] == DRIVER:
                        placements += int(float(row["Position"])) - int(float(row["GridPosition"]))
        except Exception:
            continue

    driverFeatures["Driver Past Placements"]["Std Dev"] = placements/races if races > 0 and placements != 0 else None
    #Load Past Starting Pos Avg
    placements = 0
    races = 0
    for season in range(2020,SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            schedule_path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")
            if not os.path.exists(schedule_path):
                continue
            with open(schedule_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["FullName"] == DRIVER:
                        placements += int(float(row["GridPosition"]))
                        races += 1
        except Exception:
            continue

    driverFeatures["Driver Past Placements"]["Starting Pos"] = placements/races if races > 0 and placements != 0 else None
    # Load Experiecne aroudn the track
    driverFeatures["Driver Past Placements"]["Experience"] = races if races > 0 else None

    #Load current constructors points:
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "Team Scores.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == LATEST_ROUND and is_team_equivalent(TEAM, row["TeamName"]):
                carFeatures["Team Constructors Points"] = row["Points"]

    #Load average Teammate Gap:
    recency_positions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        past_races = [row["Name"] for row in reader if int(row["Race"]) < LATEST_ROUND]

    gaps = 0
    races = 0
    for race in past_races:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{race} R.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            teammate = 0
            driver = 0
            for row in reader:
                if is_team_equivalent(TEAM, row["TeamName"]):
                    if row["FullName"] == DRIVER:
                        driver = int(float(row["Position"]))
                    else:
                        teammate = int(float(row["Position"]))
            if teammate != 0 and driver != 0:
                races += 1
            if driver == 0:
                continue

        gaps += (teammate - driver)

    driverFeatures["Teammate Gap"] = gaps/races if races > 0 else None

    # Example: number of races ahead you want to predict (0 for current race)
    round = get_round_from_race_name(season=SEASON, race_name=TRACK)
    n_ahead = round - LATEST_ROUND -1

    # Load Recency bias for starting positions:
    recency_positions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        past_races = [row["Name"] for row in reader if int(row["Race"]) <= LATEST_ROUND]

    last_races = past_races[-3:]  # last 3 races before the current round
    last_races_reversed = list(reversed(last_races))  # most recent first

    for race in last_races_reversed:
        try:
            race_path = os.path.join(base_dir, "data", str(SEASON), f"{race} R.csv")
            with open(race_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["FullName"] == DRIVER:
                        pos = int(float(row["Position"]))
                        recency_positions.append(pos)
                        break
        except Exception:
            recency_positions.append(None)

    # Make sure we have exactly 3 elements (fill with None if less)
    while len(recency_positions) < 3:
        recency_positions.append(None)

    # Shift recency positions for future races ahead
    shifted_positions = shift_recency_positions(recency_positions, n_ahead, carFeatures["Season Avg Finish"])

    # Assign recency values (Past1 = most recent, Past2 = second most, etc.)
    for i in range(3):
        key = f"Past{i+1}"
        carFeatures["Recency Finish Bias"][key] = shifted_positions[i]


    #Load current consturctors placement for the team this season
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "Team Scores.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == LATEST_ROUND and is_team_equivalent(TEAM, row["TeamName"]):
                carFeatures["Team Constructors Championship Placement"] = row["Placement"]


    # Load Average Pitstop Time
    # This Season

    time = 0
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "pitstops.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Team"] == TEAM:
                time += float(row["AveragePitStop"])
    teamFeatures["Average Pitstop Time"]["This Season"] = (time/LATEST_ROUND) if LATEST_ROUND > 0 else 0

    # Past Seasons on set Track
    total = 0
    count = 0
    for season in range(2020,SEASON):
        round = None
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), "schedule.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Name"] == TRACK:
                    round = int(row["Race"])
        if not round:
            continue
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), "pitstops.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row["Round"]) == round and row["Team"] == TEAM:
                    count += 1
                    total += float(row["AveragePitStop"])
                    break

    teamFeatures["Average Pitstop Time"]["Past on Track"] = (total / count) if count > 0 else 0


    # Load reliability (this season)
    # Load DNF rate
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), f"schedule.csv")
    checks = []
    with open(schedule_path,"r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Name"] != TRACK:
                checks.append(row["Name"])
    dnfs = 0
    for c in checks:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{c} R.csv")
        if not os.path.exists(schedule_path):
            continue
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == DRIVER:
                    if row["Status"] == "Retired":
                        dnfs += 1
    teamFeatures["Reliability"]["DNF rate"] = dnfs/len(checks) if len(checks) > 0 else 0

    #Load DNS rate
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), f"schedule.csv")
    checks = []
    with open(schedule_path,"r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Name"] != TRACK:
                checks.append(row["Name"])
    dns = 0
    for c in checks:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{c} R.csv")
        if not os.path.exists(schedule_path):
            continue
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == DRIVER:
                    if row["Status"] == "Did not start":
                        dns += 1
    teamFeatures["Reliability"]["DNS rate"] = dns/len(checks) if len(checks) > 0 else 0


    #Driver Past Placements on track
    #Load Average Placements

    placements = 0
    races = 0

    for season in range(2020,SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            schedule_path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")  
            if not os.path.exists(schedule_path):
                continue
            with open(schedule_path, "r") as file:
                reader = csv.DictReader(file)
                races += 1
                for row in reader:
                    if row["FullName"] == DRIVER:
                        placements += int(float(row["Position"]))
        except Exception:
            continue

    driverFeatures["Driver Past Placements"]["Avg"] = placements/races if races > 0 and placements != 0 else None

    #Load Car used/Average Constructors Championship
    constructors = 0
    races = 0
    for season in range(2020,SEASON):
        round = None
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), f"schedule.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Name"] == TRACK:
                    round = int(row["Race"])
                    races += 1
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), f"Team Scores.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row["Race"]) == round:
                    if is_team_equivalent(TEAM, row["TeamName"]):
                        constructors += int(row["Placement"])
                        break

    driverFeatures["Driver Past Placements"]["Car Used"] = constructors/races if races > 0 else 0

    #Load gap to teammate on track
    gaps = 0
    races = 0

    for season in range(2020, SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            schedule_path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")
            if not os.path.exists(schedule_path):
                continue
            with open(schedule_path, "r") as file:
                reader = csv.DictReader(file)
                teammate = 0
                driver = 0
                for row in reader:
                    if is_team_equivalent(TEAM, row["TeamName"]):
                        if row["FullName"] == DRIVER:
                            driver = int(float(row["Position"]))
                        else:
                            teammate = int(float(row["Position"]))
                if driver != 0 and teammate != 0:
                    races += 1

                if driver == 0:
                    continue
            gaps += (teammate - driver)
        except Exception:
            continue

    driverFeatures["Driver Past Placements"]["Teammate Gap"] = gaps/races if races > 0 else None

    #Load Wet Weather Multiplier

    #Past Seasons
    wetRaces = 0
    dryRaces = 0
    avgWet = 0
    avgDry = 0

    for season in range(2020, SEASON):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), "rain.csv")
        with open(schedule_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Rain"] == "True":
                    wetRaces += 1
                    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                    schedule_path = os.path.join(base_dir, "data", str(season), f"{row['Race']} R.csv")
                    with open(schedule_path, "r") as f:
                        r = csv.DictReader(f)
                        for driver in r:
                            if driver["FullName"] == DRIVER:
                                try:
                                    avgWet += int(float(driver["Position"]))
                                    break
                                except Exception:
                                    break
                else:
                    dryRaces += 1
                    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                    schedule_path = os.path.join(base_dir, "data", str(season), f"{row['Race']} R.csv")
                    with open(schedule_path, "r") as f:
                        r = csv.DictReader(f)
                        for driver in r:
                            if driver["FullName"] == DRIVER:
                                try:
                                    avgDry += int(float(driver["Position"]))
                                    break
                                except Exception:
                                    break
    try:
        multiplier = (avgDry/dryRaces)/(avgWet/wetRaces)
    except Exception:
        multiplier = 1

    driverFeatures["Wet Weather Multiplier"]["Prev Seasons"] = multiplier

    #This Season
    wetRaces = 0
    dryRaces = 0
    avgWet = 0
    avgDry = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "rain.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Rain"] == "True":
                wetRaces += 1
                base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{row['Race']} R.csv")
                with open(schedule_path, "r") as f:
                    r = csv.DictReader(f)
                    for driver in r:
                        if driver["FullName"] == DRIVER:
                            try:
                                avgWet += int(float(driver["Position"]))
                                break
                            except Exception:
                                break
            else:
                dryRaces += 1
                base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                schedule_path = os.path.join(base_dir, "data", str(SEASON), f"{row['Race']} R.csv")
                with open(schedule_path, "r") as f:
                    r = csv.DictReader(f)
                    for driver in r:
                        if driver["FullName"] == DRIVER:
                            try:
                                avgDry += int(float(driver["Position"]))
                                break
                            except Exception:
                                break

    try:
        multiplier = (avgDry/dryRaces)/(avgWet/wetRaces)
    except Exception:
        multiplier = 1

    driverFeatures["Wet Weather Multiplier"]["This Season"] = multiplier

    #Calculate Luck Factor

    # Setup
    avg_luck_total = 0
    avg_gain_total = 0
    positions = []
    luck_races = 0
    gain_races = 0

    for season in range(2020, SEASON):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        schedule_path = os.path.join(base_dir, "data", str(season), "* R.csv")
        race_paths = sorted(glob.glob(schedule_path))
        for path in race_paths:
            try:
                with open(path, "r") as file:
                    reader = list(csv.DictReader(file))

                    driver_row = None
                    teammate_row = None

                    for row in reader:
                        if is_team_equivalent(TEAM, row["TeamName"]):
                            if row["FullName"] == DRIVER:
                                driver_row = row
                            else:
                                teammate_row = row

                    if driver_row:
                        # Standard deviation base
                        try:
                            finish_pos = int(float(driver_row["Position"]))
                            positions.append(finish_pos)
                        except:
                            pass

                        # Gain from grid
                        try:
                            start = int(float(driver_row["GridPosition"]))
                            finish = int(float(driver_row["Position"]))
                            avg_gain_total += (start - finish)
                            gain_races += 1
                        except:
                            pass

                    if driver_row and teammate_row:
                        try:
                            drv_finish = int(float(driver_row["Position"]))
                            tmt_finish = int(float(teammate_row["Position"]))
                            avg_luck_total += (tmt_finish - drv_finish)
                            luck_races += 1
                        except:
                            pass

            except Exception as e:
                print(f"[WARN] Skipping {path}: {e}")
                continue

    # Store values
    carFeatures["Luck Factor"]["Avg Luck"] = avg_luck_total / luck_races if luck_races else 0
    carFeatures["Luck Factor"]["Avg Gain"] = avg_gain_total / gain_races if gain_races else 0
    carFeatures["Luck Factor"]["Std Dev"] = np.std(positions) if len(positions) > 1 else 0


    return winrate



#BUILD MODEL
def flatten_features(winrate):
    flat = {}

    for category in winrate:
        for key, val in winrate[category].items():
            if isinstance(val, dict):
                for subkey, subval in val.items():
                    flat[f"{category}_{key}_{subkey}"] = subval
            else:
                flat[f"{category}_{key}"] = val
    return flat
# return mapping of all drivers and teams that they drive for
def driversANDteams(season, latestRound):
    drivers = []
    teams = {}
    race = None
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(season), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == latestRound:
                race = row["Name"]
    if not race:
        return
    race_path = os.path.join(base_dir, "data", str(season), f"{race} R.csv")
    with open(race_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            drivers.append(row["FullName"])
            teams[row["FullName"]] = row["TeamName"]

    return (drivers,teams)

#return resulting score of driver at set reason and set race
def get_race_results(driver, season, race):
   
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(season), f"{race} R.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == driver:
                    try:
                        return int(float(row["Position"]))
                    except ValueError:
                        print(f"[TRAIN] Invalid position value '{row['Position']}' for {driver} at {season} {race}")
                        return None
    except FileNotFoundError:
        print(f"[TRAIN] Missing file: {path}")

#return resulting score of driver at set reason and set race
def get_quali_results(driver, season, race):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(season), f"{race} R.csv")
    try:
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == driver:
                    try:
                        return int(float(row["GridPosition"]))
                    except ValueError:
                        print(f"[TRAIN] Invalid position value '{row['GridPosition']}' for {driver} at {season} {race}")
                        return None
    except FileNotFoundError:
        print(f"[TRAIN] Missing file: {path}")


def build_quali_vector(imp_driver, imp_team, imp_season, imp_track, imp_latest_round) -> dict:
    # Baseline Data

    TRACK = imp_track
    SEASON = imp_season
    LATEST_ROUND = imp_latest_round
    DRIVER = imp_driver
    TEAM = imp_team
    # structure for model to follow and figure weights
    carFeatures = {
        "Season Avg Pos" : None,
        "Team Constructors Championship Placement": None,
        "Team Constructors Points": None,
        "Recency Bias": {"Past1": None, "Past2": None, "Past3": None},
        "Team Curr Avg": None,
        "Team Past Avg": None,
    }

    driverFeatures = {
        "Driver Past Placements": {"Avg": None, "Car Used": None, "Teammate Gap": None},
        "Wet Weather Multiplier": {"This Season": None, "Prev Seasons": None},
        "Teammate Gap": None,
        }

    QualiPos = {
        "Car": carFeatures,
        "Driver": driverFeatures
        }
    # Load Quali Model

    #Load current constructors points:
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), "Team Scores.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == LATEST_ROUND and is_team_equivalent(TEAM, row["TeamName"]):
                carFeatures["Team Constructors Points"] = row["Points"]
    # Load Teammate Gap
    #Load average Teammate Gap:
    recency_positions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        past_races = [row["Name"] for row in reader if int(row["Race"]) < LATEST_ROUND]

    gaps = 0
    races = 0
    for race in past_races:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(SEASON), f"{race} R.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            teammate = 0
            driver = 0
            for row in reader:
                if is_team_equivalent(TEAM, row["TeamName"]):
                    if row["FullName"] == DRIVER:
                        driver = int(float(row["GridPosition"]))
                    else:
                        teammate = int(float(row["GridPosition"]))
            if teammate != 0 and driver != 0:
                races += 1
            if driver == 0:
                continue

        gaps += (teammate - driver)

    driverFeatures["Teammate Gap"] = gaps/races if races > 0 else None
    # Load Recency Bias (last 3 races or as many as available)
    # Example: number of races ahead you want to predict (0 for current race)
    rnd = get_round_from_race_name(season=SEASON, race_name=TRACK)
    n_ahead = rnd - LATEST_ROUND -1
    # Load average finish for driver this season
    rounds = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), f"schedule.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) <= LATEST_ROUND:
                rounds.append(row["Name"])

    finish_sum = 0
    race_count = 0

    for round_name in rounds:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(SEASON), f"{round_name} R.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["FullName"] == DRIVER:
                    try:
                        pos = int(float(row["GridPosition"]))
                        finish_sum += pos
                        race_count += 1
                    except Exception:
                        break  # skip non-finishers or invalid data

    carFeatures["Season Avg Pos"] = finish_sum / race_count if race_count > 0 else 0
    # Load Recency bias for starting positions:
    recency_positions = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    schedule_path = os.path.join(base_dir, "data", str(SEASON), "schedule.csv")
    with open(schedule_path, "r") as file:
        reader = csv.DictReader(file)
        past_races = [row["Name"] for row in reader if int(row["Race"]) <= LATEST_ROUND]

    last_races = past_races[-3:]  # last 3 races before the current round
    last_races_reversed = list(reversed(last_races))  # most recent first

    for race in last_races_reversed:
        try:
            race_path = os.path.join(base_dir, "data", str(SEASON), f"{race} R.csv")
            with open(race_path, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["FullName"] == DRIVER:
                        pos = int(float(row["GridPosition"]))
                        recency_positions.append(pos)
                        break
        except Exception:
            recency_positions.append(None)

    # Make sure we have exactly 3 elements (fill with None if less)
    while len(recency_positions) < 3:
        recency_positions.append(None)

    # Shift recency positions for future races ahead
    shifted_positions = shift_recency_positions(recency_positions, n_ahead, carFeatures["Season Avg Pos"])

    # Assign recency values (Past1 = most recent, Past2 = second most, etc.)
    for i in range(3):
        key = f"Past{i+1}"
        QualiPos["Car"]["Recency Bias"][key] = shifted_positions[i]



    #Load current consturctors placement for the team this season
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), f"Team Scores.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) == LATEST_ROUND and is_team_equivalent(TEAM, row["TeamName"]):
                carFeatures["Team Constructors Championship Placement"] = int(row["Placement"])
                break

    #Load Team Curr Avg Qualis
    rounds = []
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), f"schedule.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row["Race"]) <= LATEST_ROUND:
                rounds.append(row["Name"])

    finish_sum = 0
    race_count = 0

    for round_name in rounds:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(SEASON), f"{round_name} R.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if is_team_equivalent(TEAM, row["TeamName"]):
                    try:
                        pos = int(float(row["GridPosition"]))
                        finish_sum += pos
                        race_count += 1
                    except Exception:
                        break  # skip non-finishers or invalid data

    carFeatures["Team Curr Avg"] = finish_sum / race_count if race_count > 0 else 0

    # Team Past Avgs on Track
    placements = 0
    races = 0

    for season in range(2020, SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")
            if not os.path.exists(path):
                continue

            with open(path, "r") as file:
                reader = csv.DictReader(file)
                found = False  # only increment races if team is found

                for row in reader:
                    if is_team_equivalent(TEAM, row["TeamName"]):

                        try:
                            placements += int(float(row["GridPosition"]))
                            found = True
                        except ValueError:
                            continue

                if found:
                    races += 1

        except Exception:
            continue

    carFeatures["Team Past Avg"] = placements / races if races > 0 else 0

    #Driver Past Placements on track
    #Load Average Placements

    placements = 0
    races = 0

    for season in range(2020, SEASON):
        path = f"data/{season}/{TRACK} R.csv"
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r") as file:
                reader = csv.DictReader(file)
                found = False
                for row in reader:
                    if row["FullName"].strip() == DRIVER.strip():
                        try:
                            pos = int(float(row["GridPosition"]))
                            if pos > 0:  # Ignore invalid positions
                                placements += pos
                                races += 1
                                found = True
                                break  # Stop reading once driver is found
                        except:
                            break
                # races += 1 should *only* happen when driver is found and position is valid
        except Exception as e:
            print(f"[WARN] Skipping {season} {TRACK} for {DRIVER}: {e}")
            continue

    driverFeatures["Driver Past Placements"]["Avg"] = placements / races if races > 0 else None
    #Load Car used/Average Constructors Championship
    constructors = 0
    races = 0
    for season in range(2020,SEASON):
        round = None
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(season), "schedule.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Name"] == TRACK:
                    round = int(row["Race"])
                    races += 1
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(season), "Team Scores.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row["Race"]) == round:
                    if is_team_equivalent(TEAM, row["TeamName"]):
                        constructors += int(row["Placement"])
                        break

    driverFeatures["Driver Past Placements"]["Car Used"] = constructors/races if races > 0 else 0

   # Load gap to teammate on track
    gaps = 0
    races = 0

    for season in range(2020, SEASON):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
            path = os.path.join(base_dir, "data", str(season), f"{TRACK} R.csv")
            if not os.path.exists(path):
                continue

            with open(path, "r") as file:
                reader = list(csv.DictReader(file))  # Cache rows

            currTeam = next((row["TeamName"] for row in reader if row["FullName"] == DRIVER), None)
            if currTeam is None:
                continue

            teammate = None
            driver = None
            for row in reader:
                if is_team_equivalent(currTeam, row["TeamName"]):
                    if row["FullName"] == DRIVER and row["GridPosition"] != "NaN":
                        driver = int(float(row["GridPosition"]))
                    elif row["FullName"] != DRIVER and row["GridPosition"] != "NaN":
                        teammate = int(float(row["GridPosition"]))

            if driver is not None and teammate is not None:
                races += 1
                gaps += (teammate - driver)
            else:
                print(f"[WARN] {season} — Missing teammate or driver for {DRIVER} in team {currTeam}")

        except Exception as e:
            print(f"[ERROR] {season}: {e}")

    driverFeatures["Driver Past Placements"]["Teammate Gap"] = gaps / races if races > 0 else None
        #Load Wet Weather Multiplier

    #Past Seasons
    wetRaces = 0
    dryRaces = 0
    avgWet = 0
    avgDry = 0

    for season in range(2020, SEASON):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
        path = os.path.join(base_dir, "data", str(season), f"rain.csv")
        with open(path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Rain"] == "True":
                    wetRaces += 1
                    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                    path = os.path.join(base_dir, "data", str(season), f"{row['Race']} R.csv")
                    with open(path, "r") as f:
                        r = csv.DictReader(f)
                        for driver in r:
                            if driver["FullName"] == DRIVER:
                                try:
                                    avgWet += int(float(driver["GridPosition"]))
                                    break
                                except Exception:
                                    break
                else:
                    dryRaces += 1
                    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                    path = os.path.join(base_dir, "data", str(season), f"{row['Race']} R.csv")
                    with open(path, "r") as f:
                        r = csv.DictReader(f)
                        for driver in r:
                            if driver["FullName"] == DRIVER:
                                try:
                                    avgDry += int(float(driver["GridPosition"]))
                                    break
                                except Exception:
                                    break
    try:
        multiplier = (avgDry/dryRaces)/(avgWet/wetRaces)
    except Exception:
        multiplier = 1

    driverFeatures["Wet Weather Multiplier"]["Prev Seasons"] = multiplier

    #This Season
    wetRaces = 0
    dryRaces = 0
    avgWet = 0
    avgDry = 0

    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
    path = os.path.join(base_dir, "data", str(SEASON), f"rain.csv")
    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Rain"] == "True":
                wetRaces += 1
                base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                path = os.path.join(base_dir, "data", str(SEASON), f"{row['Race']} R.csv")
                with open(path, "r") as f:
                    r = csv.DictReader(f)
                    for driver in r:
                        if driver["FullName"] == DRIVER:
                            try:
                                avgWet += int(float(driver["GridPosition"]))
                                break
                            except Exception:
                                break
            else:
                dryRaces += 1
                base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of model.py
                path = os.path.join(base_dir, "data", str(SEASON), f"{row['Race']} R.csv")
                with open(path, "r") as f:
                    r = csv.DictReader(f)
                    for driver in r:
                        if driver["FullName"] == DRIVER:
                            try:
                                avgDry += int(float(driver["GridPosition"]))
                                break
                            except Exception:
                                break

    try:
        multiplier = (avgDry/dryRaces)/(avgWet/wetRaces)
    except Exception:
        multiplier = 1

    driverFeatures["Wet Weather Multiplier"]["This Season"] = multiplier

    return QualiPos
