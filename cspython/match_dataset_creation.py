import sys
from cspython.merging_processing import combine_dfs
sys.setrecursionlimit(15000)
import numpy as np
import pandas as pd
#############################################################################################################
# match_dataset_creation.py comes in three parts.
# 1.the creation of columns using the unchanged player data dataset that comes from merging_processing.py. "player_based_column_making(data)"
# 2.the grouping of player data into match data  "apply_nummeric_and_group_as_match(data)"
# 3.the creation of historic columns after grouping the dataset, by match_id. "create_historic_data(data)"


def create_opponent_team_col(data): # creates a column that gives the name of the opponent of the team in that row
    data.loc[:,'player_team_opponent'] = np.nan
    data.loc[(data['team_A_name'] != data['player_team_name']),'player_team_opponent'] = data.loc[:,'team_A_name']
    data.loc[(data['team_B_name'] != data['player_team_name']),'player_team_opponent'] = data.loc[:,'team_B_name']
    return data


def create_fwa_dr_columns(data, col_list):  # first kill , awp kills, who killed who, divided by rounds
    columns = pd.Series(data.columns)
    for a in col_list:
        col = columns[columns.str.contains(a)]
        data[a + '_sum_dr'] = data[col].convert_objects(convert_numeric=True).sum(axis=1) / (
        data['team_A_score'] + data['team_B_score']) * 100
    data.loc[:, data.columns != 'date'] = data.loc[:, data.columns != 'date'].apply(pd.to_numeric, errors='ignore')
    return data


def create_player_columns(data): # creates the columns that represents if who is playing for the team for each match
    names = data.nicknames.unique()
    for a in names:
        data.loc[:, a] = 0
        data.loc[data.loc[:, 'nicknames'] == a, a] = 5  # its 5 so that when you group by team it becomes 1
    return data

def player_based_column_making(data): # these are the functions that are non historic and arent grouped by match_id
    col_list = ['first_kills', 'who_kill_who', 'awp_kills']
    data = create_opponent_team_col(data)
    data = create_fwa_dr_columns(data, col_list)
    data = create_player_columns(data)
    return data

def apply_nummeric_and_group_as_match(data): #make everything numeric and create the grouping necessary for historic functions
    r = data.loc[:, data.columns != 'date'].apply(pd.to_numeric, errors='ignore')
    r['date'] = data.date
    data = r
    data = data.fillna(0)
    data_match = data.groupby(['match_id', 'player_team_name', 'date', 'team_A_name', 'team_B_name', 'series_id', 'map', 'winner_of_match', 'loser_of_match','player_team_opponent']).mean()
    data_match = pd.DataFrame(data_match)
    data_match = data_match.reset_index()
    return data_match

def create_matches_count(data):  # how many matches a team has played
    teams = list(data.player_team_name.unique())
    new_group = pd.DataFrame()
    for a in teams:
        data_team = data.loc[data.loc[:, 'player_team_name'] == a,].sort_values(by='date', ascending=True)
        grouping = data_team.groupby(['player_team_name', 'date', 'match_id'])['ADR'].count()
        grouping = pd.DataFrame(grouping)
        grouping = grouping.reset_index()
        grouping.loc[:, 'ADR'] = grouping.loc[:, 'ADR'].expanding(min_periods=1, freq=None, center=False, axis=0).sum()
        grouping = grouping.rename(index=str, columns={'ADR': 'matches_played_team'})
        new_group = pd.concat([new_group, grouping])
    data = pd.merge(data, new_group, on=['player_team_name', 'match_id', 'date'])
    return data


def create_avdamage_his(data):  # column with historic average damage of individual
    teams = list(data.player_team_name.unique())
    new_group = pd.DataFrame()
    for a in teams:
        data_team = data.loc[data.loc[:, 'player_team_name'] == a,].sort_values(by='date', ascending=True)
        grouping = data_team.groupby(['player_team_name', 'date', 'match_id'])['ADR'].max()
        grouping = pd.DataFrame(grouping)
        grouping = grouping.reset_index()
        grouping.loc[:, 'ADR'] = grouping.loc[:, 'ADR'].expanding(min_periods=1, freq=None, center=False, axis=0).mean()
        grouping = grouping.rename(index=str, columns={'ADR': 'ADR_hist'})
        new_group = pd.concat([new_group, grouping])
    data = pd.merge(data, new_group, on=['player_team_name', 'match_id', 'date'])
    return data


def create_avdamage_map_his(data):  # historic average damage of individual for each map
    teams = list(data.player_team_name.unique())
    maps = list(data.map.unique())
    new_group = pd.DataFrame()
    for a in maps:
        for b in teams:
            data_team = data.loc[(data.loc[:, 'player_team_name'] == b) & (data.loc[:, 'map'] == a),].sort_values(
                by='date', ascending=True)
            grouping = data_team.groupby(['player_team_name', 'match_id'])['ADR'].max()
            grouping = pd.DataFrame(grouping)
            grouping = grouping.reset_index()
            grouping.loc[:, 'ADR'] = grouping.loc[:, 'ADR'].expanding(min_periods=1, freq=None, center=False,
                                                                      axis=0).mean()
            grouping = grouping.rename(index=str, columns={'ADR': 'ADR_hist_on_map'})
            new_group = pd.concat([new_group, grouping])

    data = pd.merge(data, new_group, on=['match_id', 'player_team_name'])

    return data

def create_fwadr_his(data, col_list): # historic first/awp/who kills divided by rounds
    teams = list(data.player_team_name.unique())
    for b in col_list:
        new_group = pd.DataFrame()
        for a in teams:
            data_team = data.loc[data.loc[:,'player_team_name'] == a, ].sort_values(by='date',ascending=True)
            grouping = data_team.groupby(['player_team_name','date','match_id'])[b+'_sum_dr'].max()
            grouping = pd.DataFrame(grouping)
            grouping = grouping.reset_index()
            grouping.loc[:,b +'_sum_dr'] = grouping.loc[:,b +'_sum_dr'].expanding(min_periods=1, freq=None, center=False, axis=0).mean()
            grouping = grouping.rename(index=str, columns={b +'_sum_dr': b + '_sum_dr_hist'})
            new_group = pd.concat([new_group, grouping])
        data = pd.merge(data, new_group, on = ['player_team_name','match_id','date'])
    return data


def create_faw_map_his(data, col_list): # historic first/awp/who kills divided by rounds for each map
    teams = list(data.player_team_name.unique())
    maps = list(data.map.unique())
    for b in col_list:
        new_group = pd.DataFrame()
        for i in maps:
            for a in teams:
                data_team = data.loc[(data.loc[:, 'player_team_name'] == a) & (data.loc[:, 'map'] == i),].sort_values(
                    by='date', ascending=True)
                grouping = data_team.groupby(['player_team_name', 'match_id'])[b + '_sum_dr'].max()
                grouping = pd.DataFrame(grouping)
                grouping = grouping.reset_index()
                grouping.loc[:, b + '_sum_dr'] = grouping.loc[:, b + '_sum_dr'].expanding(min_periods=1, freq=None,
                                                                                          center=False, axis=0).mean()
                grouping = grouping.rename(index=str, columns={b + '_sum_dr': b + '_sum_dr_hist_on_map'})
                new_group = pd.concat([new_group, grouping])

        data = pd.merge(data, new_group, on=['match_id', 'player_team_name'])
    return data

def create_historic_data(data): # all the functions  that are creating match based historic data
    col_list = ['first_kills', 'who_kill_who', 'awp_kills']
    data = create_fwadr_his(data, col_list)
    data = create_matches_count(data)
    data = create_avdamage_his(data)
    data = create_avdamage_map_his(data)
    data = create_faw_map_his(data, col_list)
    return data

def match_dataset_creation(data):  #creates player based columns, then groups to allow for historic match based columns
    data = player_based_column_making(data)
    data = apply_nummeric_and_group_as_match(data)
    data = create_historic_data(data)
    return data

if __name__ == '__main__':
    #data = combine_dfs(overview, big_data)
    #data = match_dataset_creation(data)

    pass