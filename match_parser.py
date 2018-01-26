from itertools import product
from bs4 import BeautifulSoup, Comment
import urllib3
import time
import re
import pprint
import multiprocessing


THREADNUM = 8

LINK = 'https://www.pro-football-reference.com'
MATCHWEEK_LINK = LINK + '/years/{YEAR}/week_{WEEK}.htm'

YEARS = range(2015, 2018)
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


def get_offense_player_stats_from_rows(rows):
    stats_list = []
    for statline in rows:
        name_group = re.match('.*<a href=\"/players/./(.*).htm\">(.*)</a>.*', statline)
        id, name = name_group.group(1), name_group.group(2)
        stats = re.findall('<td class=\"right \" data-stat=\"(.*?)\" >([0-9\.]*?)</td>', statline)
        stats_list.append({'player_id': id, 'player_name': name, 'stats': dict(stats)})
    return stats_list


def get_offense_stats(offense):
    table = get_commented_table_from_div(offense)
    away, home = table.split('<tr class="thead">')
    away_rows = re.findall('<tr >.*</tr>', away)
    home_rows = re.findall('<tr >.*</tr>', home)
    away_team_player_stats = get_offense_player_stats_from_rows(away_rows)
    home_team_player_stats = get_offense_player_stats_from_rows(home_rows)

    return {'away_team_player_stats': away_team_player_stats, 'home_team_player_stats': home_team_player_stats}


def get_data_from_match(match_link):

    match_soup = get_soup_from_link(match_link)
    scorebox = match_soup.find('div', {'class': 'scorebox'})
    additional_div = match_soup.find('div', {'id': 'all_game_info'})
    offense_div = match_soup.find('div', {'id': 'all_player_offense'})

    scorebox_info =get_match_info_from_scorebox(scorebox)
    additional_info = get_additional_match_info(additional_div)
    player_stats = get_offense_stats(offense_div)

    # add more individual stats
    match_info = {**scorebox_info, **additional_info}
    match_info = {**match_info, **player_stats}
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
    manager = multiprocessing.Manager()
    threads = []
    matches_by_week = manager.list()
    for id in range(THREADNUM):
        threads.append(multiprocessing.Process(target=get_info_for_thread, args=(game_links_splits.pop(), matches_by_week)))

    _ = [thread.start() for thread in threads]
    _ = [thread.join() for thread in threads]
    all_matches.append({'year': year, 'week': week, 'matches': list(matches_by_week)})
    print('%s Week %s Done.' % (year, week))


with open('2015_2017.data', 'w+') as out_file:
    pp = pprint.PrettyPrinter(indent=4, stream=out_file)
    pp.pprint(all_matches)
print(time.time()-start_time)