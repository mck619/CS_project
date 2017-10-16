import pandas as pd


def get_series(big_data):
    return big_data[big_data.keys()[0]]

def get_average_teamrounds(team_big_data, team, map_name, ct_map_ratio):  # the unpickled big_data file for the specific team, team name, mapname
    total_t_rounds = 0
    total_ct_rounds = 0
    match_count = 0
    for key in team_big_data.keys():  # this loops through the keys
        series = team_big_data[key]
        for i in range(0, len(series['matches'])):  # this loops through the matches  bo1 bo3 bo5
            t_rounds = 0
            ct_rounds = 0
            if series['matches'][i]['map'].loc[1] == map_name:  # this checks to see if its the map name you are looking for
                try:
                    lc = series['matches'][i][['winner', 'side_winner']].loc[0:30]  # this makes sure the score stops at 15/15
                    try:
                        rounds_counts = lc.loc[lc['winner'] == team]['side_winner'].value_counts()  # this collects the rounds
                        ct_rounds = rounds_counts['CT']
                        t_rounds = rounds_counts['T']
                    except:  # this is necessary since sometimes a team doesnt get any rounds on a specific side.
                        if lc.loc[lc['winner'] == team].iloc[0]['side_winner'] == 'CT':
                            ct_rounds = lc.loc[lc['side_winner'] == team]['side_winner'].count()
                        else:
                            t_rounds = lc.loc[lc['side_winner'] == team]['side_winner'].count()

                except:  # if this prints it means something with the key doesnt work with this function
                    print key

                total_t_rounds = total_t_rounds + t_rounds  # this totals the t side rounds
                total_ct_rounds = total_ct_rounds + ct_rounds  # this totals the ct side rounds
                match_count = match_count + 1  # this is a ticker for how many matches on the map it has found

    ct_rounds_average = float(total_ct_rounds) / match_count  # this collects the averages
    t_rounds_average = float(total_t_rounds) / match_count
    final_difference = ct_rounds_average + t_rounds_average - 15  # this gets the average total rounds they get
    ct_side = ct_rounds_average - ct_map_ratio  # this compares their ct_side with the expected big data average
    t_side = t_rounds_average - (15 - ct_map_ratio)  # this compares their ct_side with the expected big data average
    return {
        'average_rounds': [map_name, match_count, final_difference, t_side, ct_side]
    }

def roster_match(big_data, team_name, cur_roster):
    #this returns a series, the index is the series id number and the value is the number of roster matches compared to thier current roster
    matches = pd.Series(name='num_matches')
    for idx, series in big_data.iteritems():

        if series['scoreboards'][0][0].columns[0] == team_name:
            r = series['scoreboards'][0][0].loc[:, team_name].tolist()
        else:
            r = series['scoreboards'][1][0].loc[:, team_name].tolist()
        r = [get_alias(raw_name) for raw_name in r]
        num_matches = count_matches(r, cur_roster)
        matches.loc[idx] = num_matches

    return matches


def get_alias(raw_name):
    return str(raw_name.split("'")[1])

def count_matches(r, cur_roster):
    c=0
    for name in r:
        if name in cur_roster:
            c+=1
    return c


def create_team_match_overview(big_data, team):
    team_match_overview = pd.DataFrame(columns=['series_id', 'match_id', 'map', 'team', 'opponent', 't_wins',
                                                't_rounds_played', 'ct_wins', 'ct_rounds_played', 'played_first', 'result'])
    for s_id, series in big_data.iteritems():
        for match in series['matches']:
            map_name = match.iloc[0, 0]
            m_id = match.ix[1, 'match_id']
            teams = match.columns[10:12].str.slice(stop=-5).tolist()
            teams.remove(team)
            opponent = teams[0]
            if series['match_overview'].loc[series['match_overview'].match_id == m_id, 'winner'].tolist()[0] == team:
                result = 'Win'
            else:
                result = 'Loss'
            ct_wins, ct_rounds_played, t_wins, t_rounds_played, played_first = match_win_counts(match, team)
            team_match_overview.loc[len(team_match_overview), :] = (s_id,
                                                                    m_id,
                                                                    map_name,
                                                                    team,
                                                                    opponent,
                                                                    t_wins,
                                                                    t_rounds_played,
                                                                    ct_wins,
                                                                    ct_rounds_played,
                                                                    played_first,
                                                                    result)

    return team_match_overview


def match_win_counts(match, team):
    map_name = match.iloc[0, 0]
    m_id = match.ix[1, 'match_id']
    t_rounds_played = match.loc[:, 'T'].value_counts()[team]
    t_wins = len(match.loc[(match.loc[:, 'T'] == team) & (match.winner == team), :])
    ct_rounds_played = match.CT.value_counts()[team]
    ct_wins = len(match.loc[(match.CT == team) & (match.winner == team), :])

    if match.ix[1, 'CT'] == team:
        played_first = 'CT'
    else:
        played_first = 'T'

    return ct_wins, ct_rounds_played, t_wins, t_rounds_played, played_first