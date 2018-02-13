import json
import pandas as pd
from collections import defaultdict

filename = '2017_regular_season.json'


with open(filename, 'r') as handle:
    parsed = json.load(handle)

lines = defaultdict()
for game_week in parsed:
    year = game_week['year']
    week = game_week['week']
    games = game_week['matches']

    for game in games:
        away_team_coach = game['away_team_coach']
        away_team = game['away_team']
        away_team_score = game['away_team_score']
        home_team_coach = game['home_team_coach']
        home_team = game['home_team']
        home_team_score = game['home_team_score']
        match_date = game['match_date']
        attendance = game['attendance']
        roof = game['roof']
        over_under = game['over_under']
        try:
            weather = game['weather']
        except:
            weather = None
        length_of_game = game['length_of_game']
        surface = game['surface']
        stadium = game['stadium']
        match_start_time = game['match_start_time']
        vegas_line = game['vegas_line']
        won_toss = game['won_toss']

        away_team_short = ''.join(map(lambda x: x[:2], away_team.split(' ')))
        home_team_short = ''.join(map(lambda x: x[:2], home_team.split(' ')))
        match_id = str(year) + str(week) + away_team_short.upper() + home_team_short.upper()

        lines.setdefault('match_id', []).append(match_id)
        lines.setdefault('away_team', []).append(away_team)
        lines.setdefault('home_team', []).append(home_team)
        lines.setdefault('away_team_coach', []).append(away_team_coach)
        lines.setdefault('home_team_coach', []).append(home_team_coach)
        lines.setdefault('away_team_score', []).append(away_team_score)
        lines.setdefault('home_team_score', []).append(home_team_score)
        lines.setdefault('match_date', []).append(match_date)
        lines.setdefault('attendance', []).append(attendance)
        lines.setdefault('roof', []).append(roof)
        lines.setdefault('over_under', []).append(over_under)
        lines.setdefault('weather', []).append(weather)
        lines.setdefault('length_of_game', []).append(length_of_game)
        lines.setdefault('surface', []).append(surface)
        lines.setdefault('stadium', []).append(stadium)
        lines.setdefault('vegas_line', []).append(vegas_line)
        lines.setdefault('match_start_time', []).append(match_start_time)
        lines.setdefault('won_toss', []).append(won_toss)

data = pd.DataFrame(lines)
data.to_csv('2017.csv', index=False)
