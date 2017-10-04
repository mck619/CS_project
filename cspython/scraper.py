import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import datetime
import urlparse
import os


def get_teamID(team_name):
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    team_info = pd.read_csv(os.path.join(dir_path,'scrapped_data','team_info.csv'), index_col=0)
    teamID = team_info.loc[team_info.team_name == team_name, 'team_id'].tolist()[0]
    return teamID


def get_soup(url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url,headers=hdr)
    page = urllib2.urlopen(req)
    time.sleep(5)
    soup = BeautifulSoup(page)
    return soup


def get_tables(url):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=hdr)
    time.sleep(5)
    tables = pd.read_html(r.text, header=0)
    return tables


def get_match_urls(params):
    done = False
    params['offset'] = 0
    urls = []
    while not done:
        match_page = "https://www.hltv.org/results?offset={offset}&content=demo&team={teamID}&startDate={" \
                     "startDate}&endDate={endDate}".format(
            **params)
        soup = get_soup(match_page)
        matches = soup.find_all("div", class_='results-all')

        if len(matches) == 0:
            break

        results = matches[0].find_all("a", class_="a-reset")
        urls += ['https://www.hltv.org' + result['href'] for result in results]
        if len(urls) % 100 != 0:
            done = True
        else:
            params['offset'] += 100
    del params['offset']
    return urls


#################################### HEATMAP FUNCTIONS ################################################
def generate_heatmap_url(stats_page_url):
    #todo: make this dynamic so we can pull other types of heatmaps eventually
    heatmap_suffix = '?showKills=true&showDeaths=false&firstKillsOnly=false&allowEmpty=false&showKillDataset=true&showDeathDataset=true'
    heatmap_url = stats_page_url.replace('/matches/', '/matches/heatmap/') + heatmap_suffix
    return heatmap_url


def get_heatmap(site):
    soup = get_soup(site)
    divs = soup.find_all('div', class_='heatmap heatmap-data')
    heatmap_1 = divs[0]['data-heatmap-config']
    heatmap_2 = divs[1]['data-heatmap-config']
    return{
            "heat_maps" : [heatmap_1, heatmap_2]
        }


def parse_heatmap(site):
    soup = get_soup(site)
    try:                         #this section decides whether or not its a 3 map 2 map or 1map series
        match_3 = "No match_3"
        best_of_three_data = soup.find_all("div", class_ ="columns")[0]  # all dictated on whether or not
        links = []                                                       #this find_all finds the unique 'columns'
        for link in best_of_three_data.find_all('a'):
            links.append(link.get("href"))
        site1 = "https://www.hltv.org" + str(links[1])
        site2 = "https://www.hltv.org" + str(links[2])
        try:
            site3 = "https://www.hltv.org" + str(links[3])
            match_3 = get_heatmap(site3)
        finally:
            match_1 = get_heatmap(site1)
            match_2 = get_heatmap(site2)
            return {
                "match_1": match_1,
                "match_2": match_2,
                "match_3": match_3
            }
    except:
        match_1 = get_heatmap(site)
        return{
            "match_1": match_1
        }

#################################### PREFORMANCE PAGE FUNCTIONS #######################################

def get_performance_data(site):
    tables = get_tables(site)
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


def parse_stats_performance_page(url):
    # site page example "https://www.hltv.org/stats/matches/performance/mapstatsid/52325/immortals-vs-cloud9"
    # THIS THE STATS/PERFORMANCE PAGE
    soup = get_soup(url)
    try:  # this section decides whether or not its a 3 map 2 map or 1map series
        match_3 = "No match_3"
        best_of_three_data = soup.find_all("div", class_="columns")[0]  # all dictated on whether or not
        links = []  # this find_all finds the unique 'columns'
        for link in best_of_three_data.find_all('a'):
            links.append(link.get("href"))
        site1 = "https://www.hltv.org" + str(links[1])
        site2 = "https://www.hltv.org" + str(links[2])
        try:
            site3 = "https://www.hltv.org" + str(links[3])
            match_3 = get_performance_data(site3)
        finally:
            match_1 = get_performance_data(site1)
            match_2 = get_performance_data(site2)
            return {
                "match_1": match_1,
                "match_2": match_2,
                "match_3": match_3
            }
    except:
        match_1 = get_performance_data(url)
        return {
            "match_1": match_1
        }

#######################Stats page functions###############################
def parse_stats_page(url):
    # site page example  "https://www.hltv.org/stats/matches/mapstatsid/52325/immortals-vs-cloud9"
    # THIS IS THE STATS PAGE

    soup = get_soup(url)

    try:  # this section decides whether or not its a 3 map 2 map or 1map series
        match_3 = "No match_3"
        best_of_three_data = soup.find_all("div", class_="columns")[0]  # all dictated on whether or not
        links = []  # this find_all finds the unique 'columns'
        for link in best_of_three_data.find_all('a'):
            links.append(link.get("href"))
        site1 = "https://www.hltv.org" + str(links[1])
        site2 = "https://www.hltv.org" + str(links[2])
        try:
            site3 = "https://www.hltv.org" + str(links[3])
            soup = get_soup(site3)
            match_3 = get_data_page(soup)
        finally:
            soup = get_soup(site1)
            match_1 = get_data_page(soup)
            soup = get_soup(site2)
            match_2 = get_data_page(soup)
            return {
                "match_1": match_1,
                "match_2": match_2,
                "match_3": match_3
            }
    except:
        match_1 = get_data_page(soup)
        return {
            "match_1": match_1
        }


def get_data_page(soup):
    match_time = soup.find_all("div", {"class": "small-text"})
    for item in match_time:
        match_time = item.text
    match_time = datetime.datetime.strptime(match_time, '%Y-%m-%d  %H:%MMap')  # match date and time


    round_history_team = soup.find_all("div",
                                       class_="round-history-team-row")  # winner of rounds and how rounds were won
    round_history_team_a = round_history_team[0].find_all("img")
    round_history_team_b = round_history_team[1].find_all("img")
    team_a_scores = []
    for scoreing in round_history_team_a:
        team_a_scores.append([scoreing.get('title')])  # rounds that team a won
    team_b_scores = []
    for scoreing in round_history_team_b:
        team_b_scores.append([scoreing.get('title')])  # rounds that team b won
    team_a_ending = []
    for ending in round_history_team_a:
        url = urlparse.urlparse(ending.get('src'))
        base = os.path.basename(url.path)  # how team a won the round
        team_a_ending.append([os.path.splitext(base)[0]])
    team_b_ending = []
    for ending in round_history_team_b:
        url = urlparse.urlparse(ending.get('src'))
        base = os.path.basename(url.path)
        team_b_ending.append([os.path.splitext(base)[0]])  # how team b won the round
    return {
        'match_time': match_time,  # match date and time
        'team_scores': [team_a_scores, team_b_scores],  # rounds that team a won
        'team_endings': [team_a_ending, team_b_ending]  # how the team won the round
    }

###########################Overview page#################################

def parse_match_overview(url):
    #example url: 'https://www.hltv.org/matches/2314604/tyloo-vs-flash-wesg-2017-china-finals'
    #THIS IS THE MATCH OVERVIEW SITE
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

    match_data = parse_match_overview(url)
    stats_url = match_data['stats_url']
    map_stats_url = 'https://www.hltv.org/stats/matches/mapstatsid/' + stats_url.split('/')[5] + '/' + \
                    stats_url.split('/')[6]
    preformance_url = 'https://www.hltv.org/stats/matches/performance/mapstatsid/' + stats_url.split('/')[5] + '/' + \
                      stats_url.split('/')[6]

    match_data['map_stats_url'] = map_stats_url
    match_data['preformance_url'] = preformance_url

    stats_data = parse_stats_page(map_stats_url)
    preformance_data = parse_stats_performance_page(preformance_url)

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
    urls = get_match_urls(params)
    scrape(parse_all_match_data,urls)

def scrape(page_to_scrape,urls):
    matches = []
    for idx, url in enumerate(urls):
        matches.append(page_to_scrape(url))
        time.sleep(5)
        print'match {0} done'.format(idx)
        return matches

if __name__ == '__main__':

    team_name = 'TyLoo'
    startDate = '2017-08-01'
    endDate = '2017-10-01'

    matches = scrape_match_data(team_name, startDate, endDate)
    print matches

