import sys
sys.setrecursionlimit(15000)
import pandas as pd
import pdb

####################################################################################
#   Takes the multiple dataframes created by data_processing and combines them all into one large dataset
#   merging_processing does that by taking the data from data_processing, that is organized with each series
#   having its own key,  and combining each seperate dataframe in each seperate series together before merging
#   the series themselves.
#   series_data = the single series that is being merged
#   series_data_*  = is at what step in the merging of the dataframes of the series that merging_processing is on
#   data = is the final large dataframe with each series being added to it.


def merge_matches(series_data): # combines the series match data together
    for d in range(0, len(series_data['matches'])):
        if d == 0:
            series_data['matches'][d] = series_data['matches'][d].rename(index=str, columns={
                series_data['matches'][d].columns[10]: "team_A", series_data['matches'][d].columns[11]: "team_B"})
            series_data_m = series_data['matches'][d]
        else:
            series_data['matches'][d] = series_data['matches'][d].rename(index=str, columns={
                series_data['matches'][d].columns[10]: "team_A", series_data['matches'][d].columns[11]: "team_B"})
            series_data_m = pd.concat([series_data_m, series_data['matches'][d]])

    return series_data_m



def merge_overview(series_data_m, series_data): # adds matches with match_overview
    series_data['match_overview'].loc[:, 'team_A_name'] = series_data['match_overview'].columns[4]
    series_data['match_overview'].loc[:, 'team_B_name'] = series_data['match_overview'].columns[5]

    series_data['match_overview'].loc[
        (series_data['match_overview']['winner'] == series_data['match_overview'].columns[4]), 'loser_of_match'] = \
    series_data['match_overview'].team_B_name
    series_data['match_overview'].loc[
        (series_data['match_overview']['winner'] != series_data['match_overview'].columns[4]), 'loser_of_match'] = \
    series_data['match_overview'].team_A_name
    series_data['match_overview'] = series_data['match_overview'].rename(index=str, columns={
        series_data['match_overview'].columns[3]: "winner_of_match",
        series_data['match_overview'].columns[4]: "team_A_score",
        series_data['match_overview'].columns[5]: "team_B_score"})

    series_data_mo = pd.merge(series_data_m, series_data['match_overview'], on=['match_id', 'map', 'series_id'])

    return series_data_mo



def merge_scoreboards(series_data_mo, series_data): #adds matches/match_overview with scoreboards
    for i in range(len(series_data['scoreboards'][0])):
        series_data['scoreboards'][0][i]['match_num'] = i + 1
        # pdb.set_trace()
        series_data['scoreboards'][0][i]['player_team_name'] = \
        series_data_mo.loc[(series_data_mo['match_num'] == i + 1), 'team_A_name'].unique()[0]
        series_data['scoreboards'][0][i] = series_data['scoreboards'][0][i].rename(index=str, columns={
            series_data['scoreboards'][0][i].columns[0]: "team_players"})

        series_data['scoreboards'][1][i]['match_num'] = i + 1
        series_data['scoreboards'][1][i]['player_team_name'] = \
        series_data_mo.loc[(series_data_mo['match_num'] == i + 1), 'team_B_name'].unique()[0]
        series_data['scoreboards'][1][i] = series_data['scoreboards'][1][i].rename(index=str, columns={
            series_data['scoreboards'][1][i].columns[0]: "team_players"})

        new_df = pd.concat([series_data['scoreboards'][0][i], series_data['scoreboards'][1][i]])

        if i == 0:
            con_df = new_df
        else:
            con_df = pd.concat([con_df, new_df])

    series_data_mos = pd.merge(series_data_mo, con_df, how='outer', on='match_num')
    series_data_mos['nicknames'] = series_data_mos['team_players'].str.split(pat="'", expand=True)[1]
    return series_data_mos




def match_data_board_changer(series_data_mos, series_data): #adds matches/match_overview/scoreboards with player stats
    board_name = ['first_kills', 'who_kill_who', 'awp_kills']

    for idx, a in enumerate(series_data['match_data']):
        new_df = pd.DataFrame()
        for idx1, c in enumerate(board_name):
            new_board_c = pd.DataFrame()
            new_board_r = pd.DataFrame()
            names_c = a[c].set_index('Unnamed: 0').columns
            for b in names_c:
                new_board_c[b + '_' + c] = a[c].set_index('Unnamed: 0')[b].str.split(pat=':', expand=True)[0]

            names_r = a[c].set_index('Unnamed: 0').T.columns
            for b in names_r:
                new_board_r[b + '_' + c] = a[c].set_index('Unnamed: 0').T[b].str.split(pat=':', expand=True)[1]
            new_board_c['nicknames'] = new_board_c.index
            new_board_r['nicknames'] = new_board_r.index

            board_df = new_board_c.append(new_board_r)

            if idx1 == 0:
                new_df = board_df
            else:
                new_df = pd.merge(new_df, board_df, on='nicknames')
        if idx == 0:
            new_df['match_num'] = 1 + idx
            con_df = new_df
        else:
            new_df['match_num'] = 1 + idx
            try:
                con_df = con_df.append(new_df, ignore_index=True)
            except:
                print con_df.columns
                print new_df.columns
    con_df = con_df.loc[:, ~con_df.columns.duplicated()]

    series_data_mosm = pd.merge(series_data_mos, con_df, on=['nicknames', 'match_num'])
    return series_data_mosm

def combine_dfs(overview, big_data): #merges each series dataframe with itself and finally with every other series
    first=True
    cols = ['map','round_num','half','match_id','series_id','ending','CT','T','side_winner','winner','team_A','team_B','team_A_score','team_B_score','match_num','team_players','K-D','+/-','ADR','KAST','Rating2.0','nicknames']
    dfs = []
    for idx, series_data in big_data.iteritems():
        series_data_m = merge_matches(series_data)
        series_data_m.loc[:,"date"] = overview.loc[overview.id == idx, 'date'].values[0]
        series_data_mo = merge_overview(series_data_m, series_data)
        series_data_mos = merge_scoreboards(series_data_mo, series_data)
        series_data_mosm = match_data_board_changer(series_data_mos, series_data)
        dfs.append(series_data_mosm)
        new_cols = list(set(series_data_mosm.columns) -set(cols))
        cols += new_cols
    data = pd.concat(dfs)
    data = data.loc[:, cols]
    data = data.reset_index()
    return data
if __name__ == '__main__':
    # with open('../cspython/esl_teams.pkl', 'rb') as f:
    #     d = pkl.load(f)
    #
    # big_data = process_scrapped(d)
    # overview, big_data = big_data
    # data = combine_dfs(overview, big_data)