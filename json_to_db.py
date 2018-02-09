import json

filename = '2017_regular_season.json'


with open(filename, 'r') as handle:
    parsed = json.load(handle)

for game_week in parsed:
    year = game_week['year']
    week = game_week['week']
    games = game_week['matches']
    for game in games:
        away_team = game['away_team']
        home_team = game['home_team']
        #print('%s - Week %s: %s - %s' % (year,week, away_team, home_team))

        print(game.keys())