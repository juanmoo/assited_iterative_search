import yake

'''
Keyword Extractor
'''

# Default Search Params
kwe_config = {
    'lan': 'en',
    'n': 3,
    'dedupLim': 0.9,
    'dedupFunc': 'seqm',
    'windowsSize': 1,
    'top': 100, # controls number of kws extracted
    'features': None
}

def get_extractor(**kwargs):
    config = {**kwe_config}
    config.update(kwargs)
    return yake.KeywordExtractor(**config)