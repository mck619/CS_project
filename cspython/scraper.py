import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import datetime
import urlparse
import os


class modifiedSoup(BeautifulSoup):
    def __init__(self, *args, **kwargs):
        self._url = None
        BeautifulSoup.__init__(self, *args, **kwargs)

def get_teamID(team_name):
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    team_info = pd.read_csv(os.path.join(dir_path,'scrapped_data','team_info.csv'), index_col=0)
    teamID = team_info.loc[team_info.team_name == team_name, 'team_id'].tolist()[0]
    return teamID


def get_soup(url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url,headers=hdr)
    page = urllib2.urlopen(req)
    soup = modifiedSoup(page, "lxml")
    soup._url = url
    print soup._url
    time.sleep(5)
    return soup


def get_tables(url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=hdr)
    time.sleep(5)
    tables = pd.read_html(r.text, header=0)
    return tables

def get_matches_result_page_soup(params):
    match_page = "https://www.hltv.org/results?offset={offset}&content=demo&team={teamID}&startDate={" \
                 "startDate}&endDate={endDate}".format(**params)
    soup = get_soup(match_page)
    matches_soup = soup.find_all("div", class_='results-all')
    return matches_soup

def make_matches_url_loop(matches):
    urls = []
    results = matches[0].find_all("a", class_="a-reset")
    urls += ['https://www.hltv.org' + result['href'] for result in results]
    return urls


def sum_digits_in_string(digit):
    return sum(int(x) for x in digit if x.isdigit())


def make_matches_bof_loop(matches):
    bof = []
    results = matches[0].find_all("td", class_='result-score')
    bof += [result.text for result in results]
    return bof

def get_matches_result_page_urls_bof(params):
    done = False
    params['offset'] = 0

    while not done:
        matches = get_matches_result_page_soup(params)
        if len(matches) == 0:
            break

        urls = make_matches_url_loop(matches)
        bof = make_matches_bof_loop(matches)

        if len(urls) % 100 != 0:
            done = True
        else:
            params['offset'] += 100
    del params['offset']
    return {
        'urls' : urls,
        'bof' : bof
    }


def get_urls_from_columns(url):
    soup = get_soup(url)
    links = []
    bof_site = soup.find_all("div", class_="columns")[0]
    for link in bof_site.find_all('a'):
        links.append("https://www.hltv.org" + str(link.get("href")))
    return links


# currently works with get_performance_data, get_overview_data, get_heat_maps
def bof_testing(bof, url, type_of_parse):  # CANNOT BE USED WITH BASIC STATS PAGE PRIMARY_STATS_PAGE

    total_sum = sum_digits_in_string(bof)
    if total_sum > 15:
        return type_of_parse(url)
    all_matches = {}
    sites = get_urls_from_columns(url)
    if total_sum == 1:
        return 'forfeit'
    if total_sum >= 2:
        all_matches.update({'match_1': type_of_parse(sites[1]), 'match_2': type_of_parse(sites[2])})
        if total_sum >= 3:
            all_matches.update({'match_3': type_of_parse(sites[3])})
            if total_sum >= 4:
                all_matches.update({'match_4': type_of_parse(sites[4])})
                if total_sum == 5:
                    all_matches.update({'match_5': type_of_parse(sites[5])})
                else:
                    all_matches.update({'match_unknown': 'Unknown'})
    return all_matches

#################################### HEATMAP FUNCTIONS ################################################

def generate_heatmap_url(stats_page_url):
    #todo: make this dynamic so we can pull other types of heatmaps eventually
    heatmap_suffix = '?showKills=true&showDeaths=false&firstKillsOnly=false&allowEmpty=false&showKillDataset=true&showDeathDataset=true'
    heatmap_url = stats_page_url.replace('/matches/', '/matches/heatmap/') + heatmap_suffix
    return heatmap_url


def get_heatmap_data(url):
    soup = get_soup(url)
    divs = soup.find_all('div', class_='heatmap heatmap-data')
    heatmap_1 = divs[0]['data-heatmap-config']
    heatmap_2 = divs[1]['data-heatmap-config']
    return{
            "heat_maps" : [heatmap_1, heatmap_2]
        }



#################################### PERFORMANCE PAGE FUNCTIONS #######################################

def get_performance_data(url):
    tables = get_tables(url)
    total_team_kda = tables[0]
    who_kill_who = tables[1]
    first_kills = tables[2]
    awp_kills = tables[3]
    return {
        'total_team_kda': total_team_kda, # total kills deaths and assists of team
        'who_kill_who' : who_kill_who, # who killed who
        'first_kills' : first_kills, #first kill of the round
        'awp_kills' : awp_kills #awp kills
    }



#######################OVERVIEW page functions###############################

    # site page example  "https://www.hltv.org/stats/matches/mapstatsid/52325/immortals-vs-cloud9"
    # THIS IS THE OVERVIEW PAGE

def get_overview_data(url):
    soup = get_soup(url)
    match_time = get_overview_round_match_time(soup)
    round_history = soup.find_all("div", class_="round-history-team-row")
    team_scores = get_overview_round_for_loop(round_history, get_overview_round_scores)
    team_endings = get_overview_round_for_loop(round_history, get_overview_round_endings)

    return {
        'match_time': match_time,
        'team_scores': team_scores,
        'team_endings': team_endings
    }

def get_overview_round_match_time(soup):
    match_time = soup.find_all("div", {"class": "small-text"})
    for item in match_time:
        match_time = item.text
    match_time = datetime.datetime.strptime(match_time, '%Y-%m-%d  %H:%MMap')  # match date and time
    return match_time


def get_overview_round_for_loop(round_history, get_overview_round_type):
    team_info = {'team_a': [], 'team_b': []}
    for tround_a, tround_b in zip(round_history[0].find_all("img"), round_history[1].find_all("img")):
        team_info = get_overview_round_type(tround_a, tround_b, team_info)
    return team_info

def get_overview_round_scores(tround_a, tround_b, team_info):
    team_info['team_a'].append([tround_a.get('title')])  # rounds that team a won
    team_info['team_b'].append([tround_b.get('title')])
    return team_info    # rounds that team b won

def get_overview_round_endings(tround_a, tround_b, team_info):
    team_info['team_a'].append([os.path.splitext(get_base_name_from_url(tround_a))[0]])
    team_info['team_b'].append([os.path.splitext(get_base_name_from_url(tround_b))[0]])
    return team_info  # how team a won the round

def get_base_name_from_url(tround):
    url = urlparse.urlparse(tround.get('src'))
    base = os.path.basename(url.path)
    return base
###########################Stats page#################################

def get_primary_stats_page(url):
    #example url: 'https://www.hltv.org/matches/2314604/tyloo-vs-flash-wesg-2017-china-finals'
    #THIS IS THE MATCH STATS SITE
    soup = get_soup(url)

    demo_url = 'https://www.hltv.org' + soup.find_all("a", class_="flexbox left-right-padding")[0]['href']
    map_name_one = team_a_score_map_one = team_b_score_map_one = map_name_two = team_a_score_map_two = \
        team_b_score_map_two = map_name_three = team_a_score_map_three = team_b_score_map_three = 'NA'
    try:
        vetos = soup.find_all("div", class_="standard-box veto-box")[1].find_all("div")[0].find_all("div")
        vetos = [veto.text for veto in vetos]
    except:
        vetos = None

    team_name = soup.find_all("div", class_="standard-box teamsBox")[0].find_all("div", class_="teamName")
    team_info = soup.find_all("div", class_="flexbox fix-half-width-margin maps")[0].find_all("div", class_="results")

    for name in team_name[0]:
        team_a_name = name
    for name in team_name[1]:
        team_b_name = name
    best_of = soup.find_all("div", class_="padding preformatted-text")
    for best in best_of:
        best_of = best.text
    if "Best of 3" in best_of:
        map_name_one = soup.find_all("div", class_="mapname")[0]
        for name in map_name_one:
            map_name_one = name
        map_name_two = soup.find_all("div", class_="mapname")[1]
        for name in map_name_two:
            map_name_two = name
        map_name_three = soup.find_all("div", class_="mapname")[2]
        for name in map_name_three:
            map_name_three = name

        team_a_score_map_one = team_info[0].find_all("span")[0].text
        team_b_score_map_one = team_info[0].find_all("span")[2].text
        team_a_score_map_two = team_info[1].find_all("span")[0].text
        team_b_score_map_two = team_info[1].find_all("span")[2].text
        try:
            team_a_score_map_three = team_info[2].find_all("span")[0].text
            team_b_score_map_three = team_info[2].find_all("span")[2].text
        except:
            pass

    elif "Best of 1" in best_of:
        map_name_one = soup.find_all("div", class_="mapname")[0]
        for name in map_name_one:
            map_name_one = name
        team_a_score_map_one = team_info[0].find_all("span")[0].text
        team_b_score_map_one = team_info[0].find_all("span")[2].text

    elif "forfeit" in best_of:
        print "Forfeit"
    else:
        print 'New Form of match ' + url

    try:
        stats_url = 'https://www.hltv.org' + \
                [a_element['href'] for a_element in soup.find_all("a") if a_element.text == "Detailed stats"][0]
        tables = get_tables(url)
        team_a, team_b = tables[0], tables[1]
    except:
        stats_url = "NA"
        team_a = team_b = "NA"
    match_data = {
        'team_a_b': (team_a_name, team_b_name),
        'map_one': (map_name_one, team_a_score_map_one, team_b_score_map_one),
        'map_two': (map_name_two, team_a_score_map_two, team_b_score_map_two),
        'map_three': (map_name_three, team_a_score_map_three, team_b_score_map_three),
        'url': url,
        'vetos': vetos,
        'stats_url': stats_url,
        'teams': [team_a, team_b]
    }
    return match_data


def parse_all_match_data(url):
    ## this stuff should all be moved to another function which aggregates all sites

    match_data = get_primary_stats_page(url)
    stats_url = match_data['stats_url']
    map_stats_url = 'https://www.hltv.org/stats/matches/mapstatsid/' + stats_url.split('/')[5] + '/' + \
                    stats_url.split('/')[6]
    preformance_url = 'https://www.hltv.org/stats/matches/performance/mapstatsid/' + stats_url.split('/')[5] + '/' + \
                      stats_url.split('/')[6]

    match_data['map_stats_url'] = map_stats_url
    match_data['preformance_url'] = preformance_url

    stats_data = get_overview_data(map_stats_url)
    preformance_data = get_performance_data(preformance_url)

    match_data.update(stats_data)
    match_data.update(preformance_data)

    return match_data


def scrape_match_data(team_name, startDate, endDate):
    teamID = get_teamID(team_name)
    params = {
        'teamID':teamID,
        'startDate':startDate,
        'endDate':endDate
    }
    urls = get_matches_result_page_urls_bof(params)
    scrape(parse_all_match_data,urls)

def scrape(page_to_scrape,urls):
    matches = []
    for idx, url in enumerate(urls):
        matches.append(page_to_scrape(url))
        time.sleep(5)
        print'match {0} done'.format(idx)
    return matches

"""if __name__ == '__main__':

    team_name = 'TyLoo'
    startDate = '2017-08-01'
    endDate = '2017-10-01'

    matches = scrape_match_data(team_name, startDate, endDate)
    print matches
"""
