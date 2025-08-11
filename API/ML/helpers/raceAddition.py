from fileWriter import add_race
from pitstops import add_pitstops
from rain import add_rain
from WCCStandings import add_standings
SEASON = 2025
LATEST_ROUND = 14

def main():
    add_race(SEASON,LATEST_ROUND)
    add_pitstops(SEASON)
    add_rain(SEASON)
    add_standings(SEASON)


if __name__ == "__main__":
    main()
