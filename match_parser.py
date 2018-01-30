from itertools import product
from bs4 import BeautifulSoup, Comment
import urllib3
import time
import re
import pprint
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

THREADNUM = 8

LINK = 'http://www.pro-football-reference.com'
MATCHWEEK_LINK = LINK + '/years/{YEAR}/week_{WEEK}.htm'

YEARS = range(2013, 2018)
WEEKS = range(1,18)


def split_list(seq, num=THREADNUM):
    """Splits a given seq list into num number of lists"""
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last): int(last + avg)])
        last += avg

    return out


def get_commented_table_from_div(div, idx=0):
    return div.findAll(text=lambda text: isinstance(text, Comment))[idx]


def get_soup_from_link(link):
    http = urllib3.PoolManager()
    page = http.request('GET', link)

    if page.status == 200:
        return BeautifulSoup(page.data, 'html.parser')
    else:
        return None


def get_match_info_from_scorebox(scorebox):
    home_box,away_box,match_box = scorebox.find_all('div', recursive=False)
    match_box_divs = match_box.find_all('div')
    match_info = {'home_team': home_box.find('strong').text.strip(),
                  'home_team_score': home_box.find('div', {'class': 'score'}).text,
                  'home_team_standing_after': home_box.find_all('div')[3].text,
                  'home_team_coach': home_box.find('div', {'class': 'datapoint'}).find('a').text,

                  'away_team': away_box.find('strong').text.strip(),
                  'away_team_score': away_box.find('div', {'class': 'score'}).text,
                  'away_team_standing_after': away_box.find_all('div')[3].text,
                  'away_team_coach': away_box.find('div', {'class': 'datapoint'}).find('a').text,

                  'match_date': match_box_divs[0].text,
                  'match_start_time': match_box_divs[1].text.split(' ')[2], #Start Time: <time>
                  'stadium': ' '.join(match_box_divs[2].text.split(' ')[1:]).strip(),
                  'attendance': match_box_divs[3].text.split(' ')[1],
                  'length_of_game': match_box_divs[4].text.split(' ')[3]}

    return match_info

def get_additional_match_info(additional):
    # get the comments
    comment_info = get_commented_table_from_div(additional)
    rows = re.findall('<th scope=\"row\".*>.*</td>', comment_info)
    additional_info = {}
    for row in rows:
        row_data_match = re.match('<th scope=\"row\" class=\"center \" data-stat=\"info\" >(.*)</th><td class=\"center \" data-stat=\"stat\" >(.*)</td>', row)
        t = row_data_match.group(1).replace(' ', '_').replace('/', '_').lower()
        if t == 'over_under':
            additional_info[t] = row_data_match.group(2).replace('<b>(', '').replace(')</b>', '')
        else:
            additional_info[t] = row_data_match.group(2)

    return additional_info


def get_player_stats_from_rows(rows):
    stats_list = []
    for statline in rows:
        name_group = re.match('.*<a href=\"/players/./(.*).htm\">(.*)</a>.*', statline)
        id, name = name_group.group(1), name_group.group(2)
        stats = re.findall('<td class=\"right \" data-stat=\"(.*?)\" >([0-9\.]*?)</td>', statline)
        stats_list.append({'player_id': id, 'player_name': name, 'stats': dict(stats)})
    return stats_list


def get_player_stats_from_table_div(table_div, label='', two_teams=True):
    table = get_commented_table_from_div(table_div)
    if two_teams:
        away, home = table.split('<tr class="thead">')
        away_rows = re.findall('<tr >.*</tr>', away)
        home_rows = re.findall('<tr >.*</tr>', home)
        away_team_player_stats = get_player_stats_from_rows(away_rows)
        home_team_player_stats = get_player_stats_from_rows(home_rows)
        return {
            'away_team_%s_stats' % label: away_team_player_stats,
            'home_team_%s_stats' % label: home_team_player_stats}
    else:
        team_rows = re.findall('<tr >.*</tr>', table)
        team_player_stats = get_player_stats_from_rows(team_rows)
        return {label: team_player_stats}

def get_drive_stats(drive_div):
    table = get_commented_table_from_div(drive_div)
    team_rows = re.findall('<tr .*>.*</tr>', table)
    drives = {}
    for row in team_rows:
        drive_num = re.findall('<th\s*scope=\"row\s*\"\s*class="right\s*\"\s*'
                               'data-stat=\"drive_num\s*\"\s*>(.*)</th>', row)[0]
        stats = re.findall('<td class=.*?data-stat=\"(.*?)\"\s*.*?>(.*?)</td>', row)
        description, play_num = re.match('.*tip=\"(.*?)\">(.*?)</span>',
                                         stats[3][1]).groups()
        stats[3] = ('play_num', play_num)
        stats.append(('plays_description', description))
        drives[drive_num] = dict(stats)
    return drives

def get_team_stats(stats):
    table = get_commented_table_from_div(stats)
    rows = re.findall('<tr >.*</tr>', table.split('<tbody>')[1])
    team_stats = {}
    for row in rows:
        stat_line = re.match('.*data-stat=\"stat\" >(.*?)</th>.*data-stat=\"vis_stat\" >'
                             '(.*?)</td>.*data-stat=\"home_stat\" >(.*)</td></tr>', row)\
            .groups()
        team_stats[stat_line[0]] = {'away_team': stat_line[1], 'home_team': stat_line[2]}
    return team_stats

def get_data_from_match(match_link):

    match_soup = get_soup_from_link(match_link)
    scorebox = match_soup.find('div', {'class': 'scorebox'})
    additional_div = match_soup.find('div', {'id': 'all_game_info'})
    team_stats_div = match_soup.find('div', {'id': 'all_team_stats'})
    offense_div = match_soup.find('div', {'id': 'all_player_offense'})
    defense_div = match_soup.find('div', {'id': 'all_player_defense'})

    pass_div = match_soup.find('div', {'id': 'all_targets_directions'})
    rush_div = match_soup.find('div', {'id': 'all_rush_directions'})

    pass_tackles_div = match_soup.find('div', {'id': 'all_pass_tackles'})
    rush_tackles_div = match_soup.find('div', {'id': 'all_rush_tackles'})

    home_team_snapcounts_div = match_soup.find('div', {'id': 'all_home_snap_counts'})
    away_team_snapcounts_div = match_soup.find('div', {'id': 'all_vis_snap_counts'})

    home_team_drives_div = match_soup.find('div', {'id': 'all_home_drives'})
    away_team_drives_div = match_soup.find('div', {'id': 'all_vis_drives'})

    scorebox_info =get_match_info_from_scorebox(scorebox)
    additional_info = get_additional_match_info(additional_div)
    team_stats = get_team_stats(team_stats_div)
    offense_player_stats = get_player_stats_from_table_div(offense_div, 'offense_player')
    defense_player_stats = get_player_stats_from_table_div(defense_div, 'defense_player')

    pass_stats = get_player_stats_from_table_div(pass_div, 'passing_target')
    rush_direction_stats = get_player_stats_from_table_div(rush_div, 'rushing_direction')
    pass_tackle_stats = get_player_stats_from_table_div(pass_tackles_div, 'pass_tackle')
    rush_tackle_stats = get_player_stats_from_table_div(rush_tackles_div, 'rush_tackle')

    home_team_snapcount_stats = get_player_stats_from_table_div(home_team_snapcounts_div,
                                                                label='home_team_snapcount_stats',
                                                                two_teams=False)
    away_team_snapcount_stats = get_player_stats_from_table_div(away_team_snapcounts_div,
                                                                label='away_team_snapcount_stats',
                                                                two_teams=False)

    home_team_drive_stats = get_drive_stats(home_team_drives_div)
    away_team_drive_stats = get_drive_stats(away_team_drives_div)

    # add more individual stats
    match_info = {**scorebox_info, **additional_info}
    match_info = {**match_info, **team_stats}
    match_info = {**match_info, **offense_player_stats}
    match_info = {**match_info, **defense_player_stats}
    match_info = {**match_info, **pass_stats}
    match_info = {**match_info, **rush_direction_stats}
    match_info = {**match_info, **pass_tackle_stats}
    match_info = {**match_info, **rush_tackle_stats}
    match_info = {**match_info, **home_team_snapcount_stats}
    match_info = {**match_info, **away_team_snapcount_stats}
    match_info = {**match_info, **home_team_drive_stats}
    match_info = {**match_info, **away_team_drive_stats}

    return match_info


def get_info_for_thread(match_link_list, matches):
    for idx, match_link in enumerate(match_link_list):
        matches.append(get_data_from_match(match_link))

start_time = time.time()

all_matches = []
for year, week in product(YEARS, WEEKS):
    actual_link = MATCHWEEK_LINK.format(YEAR=year, WEEK=week)
    year_soup = get_soup_from_link(actual_link)
    game_links = list(map(lambda x: LINK + x.find('a')['href'], year_soup.find_all('td', {'class': 'right gamelink'})))

    # for single test
    #get_info_for_thread([game_links[0]], all_matches)

    # ###############################################################################

    # code part for threading
    #
    game_links_splits = split_list(game_links)
    #manager = multiprocessing.Manager()
    threads = []
    matches_by_week = []
    for id in range(THREADNUM):
        threads.append(threading.Thread(target=get_info_for_thread,
                                               args=(game_links_splits.pop(),
                                                     matches_by_week)))

    _ = [thread.start() for thread in threads]
    _ = [thread.join() for thread in threads]
    all_matches.append({'year': year, 'week': week, 'matches': list(matches_by_week)})
    print('%s Week %s Done.' % (year, week))


with open('2017_regular_season.data', 'w+') as out_file:
    pp = pprint.PrettyPrinter(indent=4, stream=out_file)
    pp.pprint(all_matches)
print(time.time()-start_time)