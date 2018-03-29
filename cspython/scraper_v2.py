import urllib2, requests, time, datetime, urlparse, argparse, os, sys, pdb, random, re
from bs4 import BeautifulSoup
import pandas as pd
import cPickle as pkl
from loggers import scraper_logger
from exception_logger import log_exception, add_kwargs_note_to_exception, add_soup_url_to_exception

sys.setrecursionlimit(15000)
VERBOSE_URL = False
VERBOSE_EXCEPTION_LOGGING=True
logger = scraper_logger

class modifiedSoup(BeautifulSoup):
    def __init__(self, *args, **kwargs):
        self._url = None
        BeautifulSoup.__init__(self, *args, **kwargs)

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_soup(url, sleep=True):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url, headers=hdr)
    page = urllib2.urlopen(req)
    soup = modifiedSoup(page, "lxml")
    soup._url = url
    if VERBOSE_URL:
        print soup._url
    if sleep:
        time.sleep(15 + random.randint(0, 5))
    return soup


@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('team_name')
def get_teamID(team_name):
    try:
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        team_info = pd.read_csv(os.path.join(dir_path, 'scrapped_data', 'team_info.csv'), index_col=0)
        teamID = team_info.loc[team_info.team_name == team_name, 'team_id'].tolist()[0]
        return teamID
    except:
        pass

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_tables(url, verbose=False):

        hdr = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=hdr)
        if VERBOSE_URL:
            print url
        time.sleep(15 + random.randint(0, 5))
        tables = pd.read_html(r.text, header=0)
        return tables

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_urls_from_column_divs(url):
    """
    This gets urls for stats and overview pages from series with multiple matches
    (they are contained in the first column div)
    :param url: str, url page which has the links for overview, stats or heatmap for each match in a series
    :return: list of urls, 1 for each match
    """
    try:
        soup = get_soup(url=url)
        links = []
        bof_site_columns = soup.find_all("div", class_="columns")
        for bof_site in bof_site_columns:
            for link in bof_site.find_all('a'):
                links.append("https://www.hltv.org" + str(link.get("href")))
        return links
    except:
        pass

#functions for parsing individual series data

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def scrape_series_data(url):
    """
    this is the main function for scraping data about 1 series
    example url: 'https://www.hltv.org/matches/2314604/tyloo-vs-flash-wesg-2017-china-finals'
    this is the main page that shows up when you search for a series on hltv,
    this function scrapes from all sub pages as well

    :param url: string, the primary stats page for the series to be scraped
    :return: a dict of the scraped information
    """
    soup = get_soup(url=url)
    series_data = parse_primary_stats_page(soup=soup)
    series_data['stats_data'] = get_all_match_detailed_stats(url=series_data['stats_url'], num_matches=series_data['num_matches'])
    series_data['performance_data'] = get_all_match_performance(url=series_data['performance_url'], num_matches=series_data['num_matches'])

    return series_data

##functions for parsing the detailed stats page

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_all_match_detailed_stats(url, num_matches):
    if num_matches == 1:
        return [get_detailed_stats_for_match(url=url)]
    else:
        match_stats_urls = get_urls_from_column_divs(url=url)
        detailed_match_stats = []
    for i in range(num_matches):
        detailed_match_stats.append(get_detailed_stats_for_match(url=match_stats_urls[i]))

    return detailed_match_stats

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_detailed_stats_for_match(url):
    soup = get_soup(url=url)
    detailed_stats = {'match_time':  get_match_time(soup=soup)}
    detailed_stats.update(get_round_stats(soup=soup))

    return detailed_stats

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_match_time(soup):
    match_time = soup.find_all("div", {"class": "small-text"})
    for item in match_time:
        match_time = item.text
    match_time = datetime.datetime.strptime(match_time, '%Y-%m-%d  %H:%MMap')  # match date and time
    return match_time

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_round_stats(soup):
    round_history = soup.find_all("div", class_="round-history-team-row")
    if len(round_history) > 0:
        team_scores = iterate_over_rounds(round_history, get_round_scores)
        team_endings = iterate_over_rounds(round_history, get_round_endings)
    else:
        # todo: log here even though it's not an error
        team_scores = 'no round history'
        team_endings = 'no round history'

    return {'team_scores': team_scores, 'team_endings': team_endings}

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def iterate_over_rounds(round_history, get_overview_round_type):
    team_info = {'team_a': [], 'team_b': []}
    for tround_a, tround_b in zip(round_history[0].find_all("img"), round_history[1].find_all("img")):
        team_info = get_overview_round_type(tround_a, tround_b, team_info)
    return team_info

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def get_round_scores(tround_a, tround_b, team_info):
    team_info['team_a'].append([tround_a.get('title')])  # rounds that team a won
    team_info['team_b'].append([tround_b.get('title')])  # rounds that team b won
    return team_info

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def get_round_endings(tround_a, tround_b, team_info):
    team_info['team_a'].append([os.path.splitext(get_base_name_from_url(tround_a))[0]])
    team_info['team_b'].append([os.path.splitext(get_base_name_from_url(tround_b))[0]])
    return team_info  # how team a won the round

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def get_base_name_from_url(tround):
    url = urlparse.urlparse(tround.get('src'))
    base = os.path.basename(url.path)
    return base

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_all_match_performance(url, num_matches):
    if num_matches == 1:
        return [get_performance_data(url=url)]
    else:
        match_performance_urls = get_urls_from_column_divs(url=url)
        match_performance_stats = []
    for i in range(num_matches):
        match_performance_stats.append(get_performance_data(url=match_performance_urls[i]))

    return match_performance_stats

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_performance_data(url):
    tables = get_tables(url=url)
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

# functions for pasring the primary series stats page

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def parse_primary_stats_page(soup):
    series_data = determine_series_best_of_format(soup=soup)
    series_data['scores'] = get_series_team_scores(soup=soup)
    series_data['num_matches'] = determine_number_of_matches_played(series_data)
    series_data['team_a_b'] = [series_data['scores'][0][0], series_data['scores'][1][0]]
    series_data['vetos'] = get_primary_stats_page_veto(soup=soup)

    map_names = get_primary_stats_map_name(soup=soup, num_matches=series_data['num_matches'])
    map_scores = get_primary_stats_map_scores(soup=soup, num_matches=series_data['num_matches'])
    series_data['map_scores'] = organize_map_score_data(map_names, map_scores)

    series_data['map_pool'] = get_map_pool(soup=soup)
    series_data['demo_url'] = get_demo_url(soup=soup)
    series_data['stats_url'] = get_stats_url(soup=soup)
    series_data['performance_url'] = series_data['stats_url'].replace('/matches/', '/matches/performance/')

    tables = get_tables(url=soup._url)
    series_data['team_scoreboards'] = split_tables_scoreboard(tables)

    return series_data

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def determine_number_of_matches_played(series_data):
    if series_data['best_of'] == 'forfeit':
        return False
    elif series_data['best_of'] != 1:
        num_matches = series_data['scores'][0][1] + series_data['scores'][1][1]
    else:
        num_matches = 1

    return num_matches

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_demo_url(soup):
    url = 'https://www.hltv.org' + soup.find_all("a", class_="flexbox left-right-padding")[0]['href']
    return url


@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_stats_url(soup):
    url = 'https://www.hltv.org' + [a_element['href'] for a_element in soup.find_all("a") if a_element.text == "Detailed stats"][0]
    return url


@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def split_tables_scoreboard(tables):
    team_a_scoreboards = []
    team_b_scoreboards = []
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
    return [team_a_scoreboards, team_b_scoreboards] #these tables matchup positionally with the map names coming from match_info,

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
def organize_map_score_data(map_names, map_scores):
    if map_names[0] == 'Forfeit':
        return map_names
    map_results = []
    for i in range(0, len(map_names)):
        map_results.append({'map_name': str(map_names[i]),
                           'scores': map_scores[i]})
    return map_results

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_primary_stats_map_scores(soup, num_matches):
    team_info = soup.find_all("div", class_="flexbox fix-half-width-margin maps")[0].find_all("div", class_="results")
    map_scores = []
    for i in range(num_matches):
        try:
            team_a_score = team_info[i].find_all("span")[0].text
            team_b_score = team_info[i].find_all("span")[2].text
            map_scores.append([team_a_score, team_b_score])
        except:
            map_scores.append(None)
    return map_scores

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_primary_stats_map_name(soup, num_matches):
    map_names = []
    for i in range(num_matches):
        try:
            name = soup.find_all("div", class_="mapname")[i].text
            map_names.append(name)
        except:
            map_names.append(None)
    return map_names

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def determine_series_best_of_format(soup):
    forfeit = False
    lan = False
    best_of_format = 'unknown'
    try:
        element_text = soup.find_all('div', attrs={'class': 'padding preformatted-text'})[0].text
        best_of_format = re.search(r'Best of (\d+)', element_text).groups()[0]
        lan = '(LAN)' in element_text
        if 'forfeited' in element_text:
            forfeit = re.search(r' (.*?) forfeited the match', element_text).groups()[0]
    except Exception as e:
        print 'problem determining format of: ', soup._url
        print e

    return {'best_of': int(best_of_format),
            'forfeit': forfeit,
            'lan': lan}

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_map_pool_url(soup):
    all_as = soup.find_all('a', class_="sidebar-single-line-item")
    for a in all_as:
        if a.text == 'Map pool':
            url = 'https://www.hltv.org' + a['href']
            return url
    return False

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_map_pool(soup):
    url = get_map_pool_url(soup=soup)
    if url:
        pool_page_soup = get_soup(url=url)
        all_maps = pool_page_soup.find_all('div', class_='map-pool-map-name')
        pool = [map.text for map in all_maps]
        return pool
    else:
        return None

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_primary_stats_page_veto(soup):
    try:
        vetos = soup.find_all("div", class_="standard-box veto-box")[1].find_all("div")[0].find_all("div")
        vetos = [veto.text for veto in vetos]
    except:
        vetos = []
    return vetos

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_soup_url_to_exception()
def get_series_team_scores(soup):
    score_box = soup.find_all('div', attrs={'class': 'standard-box teamsBox'})[0]
    scores = []
    for div in score_box.find_all('div'):
        if div["class"][0] == "teamName":
            cur_team = div.text
        if div["class"][0] in ("won", "lost", "tie"):
            scores.append((cur_team, int(div.text)))
    return scores

# functions for parsing multiple seres
@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def add_offset_to_match_page_url(url, offset):
    match_page = url
    match_page = match_page.split('results?')[0] + "results?offset=" + str(offset) + "&" + match_page.split('results?')[1]
    return match_page

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def query_series_urls(params=None, url=None):
    done = False
    if params is None:
        params = {}
    params['offset'] = 0
    series_urls = []
    while not done:
        # this loop iterates through multi-page query results(100 per page)
        series_urls += get_all_series_urls(params, url)
        if len(series_urls) == 0:
            break
        if len(series_urls) % 100 != 0:
            done = True
        else:
            params['offset'] += 100

    del params['offset']
    return series_urls

@log_exception(logger, verbose_exception_logging=VERBOSE_EXCEPTION_LOGGING)
@add_kwargs_note_to_exception('url')
def get_all_series_urls(params=None, url=None): # scrapes all individual series url from a query on hltv, called by query_series_urls
    if url is not None:
        match_page = add_offset_to_match_page_url(url=url, offset=params['offset'])
    else:
        if not params['teamID']:
            match_page = "https://www.hltv.org/results?offset={offset}&content=demo&startDate={" \
                         "startDate}&endDate={endDate}".format(**params)
        else:
            match_page = "https://www.hltv.org/results?offset={offset}&content=demo&team={teamID}&startDate={" \
                         "startDate}&endDate={endDate}".format(**params)
    soup = get_soup(url=match_page)
    matches_soup = soup.find_all("div", class_='results-all')

    urls = []
    for m in matches_soup:
        try:
            results = m.find_all("a", class_="a-reset")
            urls += ['https://www.hltv.org' + result['href'] for result in results]
        except:
            pass
    return urls



if __name__ == '__main__':
    #todo: argparse
    pass
