import cPickle as pkl

with open('series_data.pkl', 'rb') as f:
    s = pkl.load(f)

print s[s.keys()[0]].keys()