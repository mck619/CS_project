import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import datetime
import urlparse
import os, sys
import cPickle as pkl
import pdb
sys.setrecursionlimit(15000)


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
    if VERBOSE_URL:
        print soup._url
    time.sleep(5)
    return soup


def get_tables(url, verbose=False):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=hdr)
    if VERBOSE_URL:
        print url
    time.sleep(5)
    tables = pd.read_html(r.text, header=0)
    return tables

def get_matches_result_page_soup(params):
    if not params['teamID']:
        match_page = "https://www.hltv.org/results?offset={offset}&content=demo&startDate={" \
                     "startDate}&endDate={endDate}".format(**params)
    else:
        match_page = "https://www.hltv.org/results?offset={offset}&content=demo&team={teamID}&startDate={" \
                 "startDate}&endDate={endDate}".format(**params)

    soup = get_soup(match_page)
    matches_soup = soup.find_all("div", class_='results-all')
    return matches_soup

def make_matches_url_loop(matches):
    urls = []
    for m in matches:
        try:
            results = m.find_all("a", class_="a-reset")
            urls += ['https://www.hltv.org' + result['href'] for result in results]
        except:
            pass
    return urls


def sum_digits_in_string(digit):
    digit = digit.split()
    return sum(int(x) for x in digit if x.isdigit())


def make_matches_bof_loop(matches):
    bof = []
    try:
        results = matches.find_all("td", class_='result-score')
        bof += [result.text for result in results]
    except:
        results = matches[0].find_all("td", class_='result-score')
        bof += [result.text for result in results]
    return bof

def get_matches_result_page_urls_bof(params):
    done = False
    params['offset'] = 0
    urls = []
    bof = []
    while not done:
        matches = get_matches_result_page_soup(params)
        if len(matches) == 0:
            break

        urls += make_matches_url_loop(matches)
        if params['offset'] == 0 and not params ['teamID']:
            bof += make_matches_bof_loop(matches[len(matches)-1])
        else:
            bof += make_matches_bof_loop(matches)
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
    bof_site_columns = soup.find_all("div", class_="columns")
    #pdb.set_trace()
    for bof_site in bof_site_columns:
        for link in bof_site.find_all('a'):
            links.append("https://www.hltv.org" + str(link.get("href")))
    return links


# currently works with get_performance_data, get_overview_data, get_heat_maps
def bof_testing(bof, url, type_of_parse):  # CANNOT BE USED WITH BASIC STATS PAGE PRIMARY_STATS_PAGE
    total_sum = sum_digits_in_string(bof)
    if total_sum > 15:
        return type_of_parse(url)
    all_matches = []
    sites = get_urls_from_columns(url)
    if total_sum == 1:
        return ['Forfeit', bof]
    if total_sum >= 2:
        all_matches.append(type_of_parse(sites[1]))
        all_matches.append(type_of_parse(sites[2]))
        if total_sum >= 3:
            all_matches.append(type_of_parse(sites[3]))
            if total_sum >= 4:
                #pdb.set_trace()
                all_matches.append(type_of_parse(sites[4]))
                if total_sum == 5:
                    all_matches.append(type_of_parse(sites[5]))
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
    if len(round_history)>0:
        team_scores = get_overview_round_for_loop(round_history, get_overview_round_scores)
        team_endings = get_overview_round_for_loop(round_history, get_overview_round_endings)
    else:
        team_scores = 'no round history'
        team_endings = 'no round history'
        print 'no round history'
    return {
        'match_time': match_time,
        'team_scores': team_scores,
        'team_endings': team_endings,

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


def get_primary_stats_page_veto(soup):
    try:
        vetos = soup.find_all("div", class_="standard-box veto-box")[1].find_all("div")[0].find_all("div")
        vetos = [veto.text for veto in vetos]
    except:
        vetos = None
    return vetos

def get_primary_stats_page_tname(soup):
    team_name = soup.find_all("div", class_="standard-box teamsBox")[0].find_all("div", class_="teamName")
    for name in team_name[0]:
        team_a_name = name
    for name in team_name[1]:
        team_b_name = name
    return {
        'team_a_b': [str(team_a_name), str(team_b_name)]
    }

def get_primary_stats_bof(bof, primary_parser,soup):
    bof_sum = sum_digits_in_string(bof)
    if bof_sum == 1:
        match_info = ['Forfeit', bof]
        return match_info
    if bof_sum > 15:
        bof_sum = 1
    match_info = []
    for i in range(0,bof_sum):
        result = primary_parser(soup, i)
        if result is None:
            continue
        else:
            match_info.append(result)
    return match_info

def get_primary_stats_map_name(soup, i):
    try:
        name = soup.find_all("div", class_="mapname")[i].text
    except:
        return None
    return name

def get_primary_stats_map_scores(soup, i):
    team_info = soup.find_all("div", class_="flexbox fix-half-width-margin maps")[0].find_all("div", class_="results")
    try:
        team_a_score = team_info[i].find_all("span")[0].text
        team_b_score = team_info[i].find_all("span")[2].text
    except:
        return None
    return {
        'team_scores' : [team_a_score, team_b_score]
    }

def get_primary_organize_data(map_names, map_scores):
    if map_names[0] == 'Forfeit':
        return map_names
    match_info = []
    for i in range(0, len(map_names)):
        match_info.append({'map_name': str(map_names[i]),
                           'scores': map_scores[i]['team_scores']})

    return match_info

def split_tables_scoreboard(tables):
    team_a_scoreboards = []
    team_b_scoreboards = []
    #pdb.set_trace()
    if len(tables) <= 7:
            team_a_scoreboards.append(tables[0])
            team_b_scoreboards.append(tables[1])
    if len(tables) > 7:
        for i in range(2,len(tables)-4):
            if len(tables[i])==1:
                continue
            if i % 2 == 0:
                team_a_scoreboards.append(tables[i])
            else:
                team_b_scoreboards.append(tables[i])
    #pdb.set_trace()
    return [team_a_scoreboards, team_b_scoreboards] #these tables matchup positionally with the map names coming from match_info,

def get_primary_stats_page(url, bof):
    # example url: 'https://www.hltv.org/matches/2314604/tyloo-vs-flash-wesg-2017-china-finals'
    # THIS IS THE MATCH STATS SITE
    soup = get_soup(url)
    vetos = get_primary_stats_page_veto(soup)
    team_a_b = get_primary_stats_page_tname(soup)  # gets team names
    map_names = get_primary_stats_bof(bof, get_primary_stats_map_name, soup)  # output dependent on the best of result
    map_scores = get_primary_stats_bof(bof, get_primary_stats_map_scores,
                                       soup)  # output dependent on the best of result
    match_info = get_primary_organize_data(map_names, map_scores)
    map_pool = get_map_pool(soup)
    try:
        demo_url = 'https://www.hltv.org' + soup.find_all("a", class_="flexbox left-right-padding")[0]['href']
        stats_url = 'https://www.hltv.org' + \
                    [a_element['href'] for a_element in soup.find_all("a") if a_element.text == "Detailed stats"][0]
        tables = get_tables(url)
        team_scoreboards = split_tables_scoreboard(tables)

    except:
        demo_url = "NA"
        stats_url = "NA"
        team_a = team_b = "NA"
        team_scoreboards = "NA"
        print "something bad happened: ", url
    if vetos is None:
        vetos = []

    match_data = {
        'team_a_b': team_a_b['team_a_b'],
        'match_info': match_info,
        'url': url,
        'vetos': vetos,
        'stats_url': stats_url,
        'team_scoreboards': team_scoreboards,  #these tables matchup positionally with the map names coming from match_info,
        'demo_url':demo_url,
        'map_pool':map_pool
   }
    return match_data


def get_map_pool_url(soup):
    all_as = soup.find_all('a', class_="sidebar-single-line-item")
    for a in all_as:
        if a.text == 'Map pool':
            url = 'https://www.hltv.org' + a['href']
            return url
    return False

def get_map_pool(soup):
    url = get_map_pool_url(soup)
    if url:
        pool_page_soup = get_soup(url)
        all_maps = pool_page_soup.find_all('div', class_='map-pool-map-name')
        pool = [map.text for map in all_maps]
        return pool
    else:
        return None

def parse_all_match_data(url, bof):
    ## this stuff should all be moved to another function which aggregates all sites

    match_data = get_primary_stats_page(url,bof)
    stats_data = bof_testing(bof, match_data['stats_url'], get_overview_data)
    if isinstance(stats_data, dict):
        match_data['stats_data'] = [stats_data]
    else:
        match_data['stats_data'] = stats_data
    performance_url = match_data['stats_url'].replace('/matches/', '/matches/performance/')
    performance_data = bof_testing(bof, performance_url, get_performance_data)
    if isinstance(performance_data, dict):
        match_data['match_data'] = [performance_data]
    else:
        match_data['match_data'] = performance_data

    return match_data


def scrape_series_data(startDate, endDate, team_name=False,  verbose=False, pkl_save=False, teamID=False, offset=0):
    global VERBOSE_URL
    VERBOSE_URL = verbose
    if not teamID:
        if not team_name:
            print "date based search"
        else:
            teamID = get_teamID(team_name)
    params = {
        'teamID':teamID,
        'startDate':startDate,
        'endDate':endDate
     }
    urls_bof = get_matches_result_page_urls_bof(params)
    urls_bof['urls'] = urls_bof['urls'][offset:]
    urls_bof['bof'] = urls_bof['bof'][offset:]
    all_series, bad_matches = scrape(parse_all_match_data,urls_bof, pkl_save)
    return all_series, bad_matches

def scrape(page_to_scrape,urls_bof, pkl_save=False):
    all_series = []
    bad_matches= []
    urls = urls_bof['urls']
    bof = urls_bof['bof']
    for idx, url in enumerate(urls):
        try:
            all_series.append(page_to_scrape(url,bof[idx]))
            time.sleep(5)
            print'match {0} done'.format(idx)
            if pkl_save and idx%5==0:
                print 'last saved: ', url
                save_data(all_series, pkl_save)
        except:
            print 'bad match:', url
            bad_matches.append(url)

    return all_series, bad_matches


def save_data(matches, name):
    with open(name, 'wb') as f:
        pkl.dump(matches, f)

def make_matches_result_count(matches):
    count = 0
    results = matches[0].find_all("a", class_="a-reset")
    for result in results:
        count += 1
    return count

#THIS OUTPUTS A QUICK COUNT OF RESULTS BASED ON THE PARAMETERS
def get_result_page_match_count(team_name, startDate, endDate, verbose = False):
    done = False
    global VERBOSE_URL
    VERBOSE_URL = verbose
    teamID = get_teamID(team_name)
    params = {
        'teamID': teamID,
        'startDate': startDate,
        'endDate': endDate
    }
    params['offset'] = 0
    count = 0
    while not done:
        matches = get_matches_result_page_soup(params)
        if len(matches) == 0:
            break

        count += make_matches_result_count(matches)

        if count % 100 != 0:
            done = True
        else:
            params['offset'] += 100

    del params['offset']
    print 'There are, ', count, ' series with these parameters'



if __name__ == '__main__':


    startDate = '2017-11-12'
    endDate = '2017-11-14'
    scrape_series_data(startDate, endDate)


    # team_name = 'NRG'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)
    #
    # team_name = 'BIG'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)
    #
    # team_name = 'CLG'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)

    # team_name = 'Cloud9'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)
    #
    # team_name = 'HellRaisers'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)
    #
    # team_name = 'mousesports'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    #
    # save_data(series, filename)


    # team_name = 'Renegades'
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    # save_data(series, filename)

    # team_name = 'Renegades'
    # startDate = '2016-10-01'
    # endDate = '2017-07-22'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename)
    # save_data(series, filename)




    # team_name = 'Tempo-Storm-b'
    # teamID = 8221
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename, teamID=teamID)
    #
    # save_data(series, filename)

    # team_name = 'paiN'
    # teamID = 8079
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename, teamID=teamID)
    #
    # save_data(series, filename)
    #
    # team_name = 'ex-paiN'
    # teamID = 4773
    # startDate = '2016-10-01'
    # endDate = '2017-10-13'
    # filename = team_name + '_' + startDate + '_to_' + endDate + '.pkl'
    # series = scrape_series_data(team_name, startDate, endDate, verbose=True, pkl_save=filename, teamID=teamID)
    #
    # save_data(series, filename)
