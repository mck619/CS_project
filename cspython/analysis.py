import pandas as pd

def get_average_teamrounds(team_big_data, team, map_name):  # the unpickled big_data file for the specific team, team name, mapname
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
    return {
        'average_rounds': [ct_rounds_average, t_rounds_average, map_name, match_count]
    }


def roster_match(big_data, team_name, cur_roster):
    matches = pd.Series(name='num_matches')
    for idx, series in big_data.iteritems():

        if series['scoreboards'][0][0].columns[0] == cur_roster:
            r = series['scoreboards'][0][0].loc[:, team_name].tolist()
        else:
            r = series['scoreboards'][1][0].loc[:, team_name].tolist()
        r = [get_alias(raw_name) for raw_name in r]
        num_matches = count_matches(r, cur_roster)
        matches.loc[idx] = num_matches


def get_alias(raw_name):
    return str(raw_name.split("'")[1])

def count_matches(r, cur_roster):
    c=0
    for name in r:
        if name in cur_roster:
            c+=1
    return c