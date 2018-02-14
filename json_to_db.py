import json
import pandas as pd
from collections import defaultdict

filename = '2017_regular_season.json'


with open(filename, 'r') as handle:
    parsed = json.load(handle)

lines = pd.DataFrame()
for game_week in parsed:
    year = game_week['year']
    week = game_week['week']
    games = game_week['matches']

    for game in games:
        print(game.keys())
        game_line_dict = {}
        away_team_coach = game['away_team_coach']
        away_team = game['away_team']
        away_team_score = game['away_team_score']
        home_team_coach = game['home_team_coach']
        home_team = game['home_team']
        home_team_score = game['home_team_score']
        match_date = game['match_date']
        attendance = game['attendance'].replace(',', '')
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

        game_line_dict['match_id'] = match_id
        game_line_dict['away_team'] = away_team
        game_line_dict['home_team'] = home_team
        game_line_dict['away_team_coach'] = away_team_coach
        game_line_dict['home_team_coach'] = home_team_coach
        game_line_dict['away_team_score'] = away_team_score
        game_line_dict['home_team_score'] = home_team_score
        game_line_dict['match_date'] = match_date
        game_line_dict['attendance'] = attendance
        game_line_dict['roof'] = roof
        game_line_dict['over_under'] = over_under
        game_line_dict['weather'] = weather
        game_line_dict['length_of_game'] = length_of_game
        game_line_dict['surface'] = surface
        game_line_dict['stadium'] = stadium
        game_line_dict['vegas_line'] = vegas_line
        game_line_dict['match_start_time'] = match_start_time
        game_line_dict['won_toss'] = won_toss
        s = pd.Series(game_line_dict)
        lines = lines.append(s, ignore_index=True)


# print(lines)
# data = pd.DataFrame(lines)
# data.to_csv('game_info.2017', index=False, columns=['match_id', 'away_team', 'home_team', 'away_team_coach',
#                                               'home_team_coach', 'away_team_score', 'home_team_score',
#                                               'match_date', 'attendance', 'roof', 'weather', 'surface',
#                                               'stadium', 'match_start_time', 'length_of_game', 'won_toss',
#                                               'over_under', 'vegas_line'], header=False)
