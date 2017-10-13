import cspython.scraper
import pandas as pd
import uuid
import sys
sys.setrecursionlimit(15000)
# Each element of list returned by scrape_series_data is a dictionary containing data 1 series played by the team. They are in reverse chornological order. The elements of each series dictionary are:
# url:        the url on hltv of the Overview of the entire series
# demo_url:   the url of the demo, hosted on hltv later
# stats_url:  a url containing more detailed data about the data
#             (the scrapped data from this page is contained in stats_data)
# teams:      a dataframe containing the overall stats for each team in the series
# vetos:      the vetos in chronological order
# match_info: score and map name for each match
# team_a_b:   this provides order to the teams and match_info scores

def match_score_dataframe(series, series_id=None):
    score = pd.DataFrame(columns=['series_id', 'match_id', 'map', 'winner', series['team_a_b'][0],
                                  series['team_a_b'][1]],
                         index=range(len(series['match_info'])))
    for idx, match in enumerate(series['match_info']):

        map_name = match['map_name']
        score_a = int(match['scores'][0])
        score_b = int(match['scores'][1])
        if score_a > score_b:
            winner = series['team_a_b'][0]
        elif score_a < score_b:
            winner = series['team_a_b'][1]
        else:
            winner = 'draw'
        match_id = str(uuid.uuid4())
        score.loc[idx, :] = series_id, match_id, map_name, winner, score_a, score_b

    score.loc[:, 'match_num'] = range(1, len(score) + 1)

    return score


def round_by_round_dataframe(match_stats_data, map_name, match_id, series_id):
    winners = create_winner_column(match_stats_data['team_scores'])
    team_ending_df = create_team_ending_df(match_stats_data['team_endings'], winners)
    raw = pd.concat([team_ending_df, winners], axis=1)
    if len(raw) > 30:  # TRUNCATES OVERTIME, FIX THIS LATER
        raw = raw.iloc[:30, :]

    final = pd.DataFrame(columns=['map', 'round_num', 'half'], index=raw.index)
    final.loc[:, 'map'] = map_name
    final.loc[:, 'round_num'] = raw.index
    final.ix[:16, 'half'] = 1
    final.ix[16:, 'half'] = 2
    final.loc[:, 'match_id'] = match_id
    final.loc[:, 'series_id'] = series_id
    return pd.concat([final, raw], axis=1)


def create_winner_column(team_scores):
    team_a = pd.Series(team_scores['team_a']).apply(lambda x: x[0])
    team_b = pd.Series(team_scores['team_b']).apply(lambda x: x[0])
    raw_scores = pd.concat([team_a, team_b], axis=1)
    raw_scores = raw_scores.loc[(raw_scores.loc[:, 0] != '') | (raw_scores.loc[:, 1] != ''), :]

    team_a = raw_scores.iloc[0, 0]
    team_b = raw_scores.iloc[0, 1]

    raw_scores = raw_scores.iloc[1:, :]

    winner_col = pd.DataFrame(columns=['winner', team_a + '_wins', team_b + '_wins'], index=raw_scores.index)
    w_a = 0
    w_b = 0
    for idx, row in raw_scores.iterrows():
        if row.iloc[0] == '':
            winner = team_b
            w_b += 1
        else:
            winner = team_a
            w_a += 1
        winner_col.loc[idx, ['winner', team_a + '_wins', team_b + '_wins']] = winner, w_a, w_b
    return winner_col


def create_team_ending_df(team_endings, winners):
    team_a_name, team_b_name = winners.columns[1][:-5], winners.columns[2][:-5]

    team_a = pd.Series(team_endings['team_a']).apply(lambda x: x[0])
    team_b = pd.Series(team_endings['team_b']).apply(lambda x: x[0])
    raw_endings = pd.concat([team_a, team_b], axis=1)
    raw_endings = raw_endings.loc[(raw_endings.loc[:, 0] != 'emptyHistory') | (raw_endings.loc[:, 1] != 'emptyHistory'),
                  :]
    raw_endings = raw_endings.iloc[1:, :]
    endings = pd.DataFrame(columns=['ending', 'CT', 'T', 'side_winner'], index=raw_endings.index)

    if (('t_win' in team_a.iloc[:16])
        or ('ct_win' in team_a.iloc[:16])
        or ('ct_win' in team_a.iloc[16:])
        or ('t_win' in team_a.iloc[16:])):
        endings.ix[:16, 'T'] = team_b_name
        endings.ix[:16, 'CT'] = team_a_name
        endings.ix[16:, 'T'] = team_a_name
        endings.ix[16:, 'CT'] = team_b_name
    else:
        endings.ix[:16, 'T'] = team_a_name
        endings.ix[:16, 'CT'] = team_b_name
        endings.ix[16:, 'T'] = team_b_name
        endings.ix[16:, 'CT'] = team_a_name

    endings.loc[:, 'ending'] = raw_endings.apply(lambda x: x.iloc[0] if x.iloc[0] != 'emptyHistory' else x.iloc[1],
                                                 axis=1)
    endings.loc[:, 'side_winner'] = endings.apply(
        lambda x: 'T' if x.loc['T'] == winners.loc[x.name, 'winner'] else 'CT', axis=1)
    return endings


def series_overview_dataframe(all_series):
    all_series_overview = pd.DataFrame(columns=['id', 'date', 'team_a',
                                                'team_b', 'url', 'stats_url',
                                                'demo_url'])
    for s in all_series:
        demo_url = s['demo_url']
        stats_url = s['stats_url']
        url = s['url']
        date = s['stats_data'][0]['match_time']
        team_a = s['team_a_b'][0]
        team_b = s['team_a_b'][1]
        series_uuid = str(uuid.uuid4())
        all_series_overview.loc[len(all_series_overview), :] = (
            series_uuid, date, team_a, team_b, url, stats_url, demo_url)

    return all_series_overview


def process_scrapped(all_series):
    overview = series_overview_dataframe(all_series)
    series_data = {}

    for s_id, s in zip(overview.id, all_series):
        match_overview = match_score_dataframe(s, s_id)
        map_pool = s['map_pool']
        vetos = s['vetos']
        matches = []
        for m_id, m, map_name in zip(match_overview.match_id, s['stats_data'], match_overview.map):
            df = round_by_round_dataframe(m, map_name, m_id, s_id)
            matches.append(df)

        series_data[s_id] = {
            'match_overview': match_overview,
            'map_pool': map_pool,
            'vetos': vetos,
            'scoreboards': s['team_scoreboards'],
            'matches': matches}
    return overview, series_data

if __name__ == '__main__':

    series = cspython.scraper.scrape_series_data('NRG', '2017-10-01', '2017-10-03', verbose=False)
    overview, series_data = process_scrapped(series)
    print overview
