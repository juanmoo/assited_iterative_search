import requests
from Bio import Entrez
from urllib import parse
from bs4 import BeautifulSoup as Soup
import pandas as pd
import re

'''
Search
'''

# Default Search Constants
default_search_config = {
    'email': '',
    'db': 'pubmed',
    'retmode': 'xml',
    'sort': 'relevance',
    'retmax': 100
}

# Get PMIDs based on query -- database search order does not match pubmed search
def search_v1(query, **kwargs):
    config = {**default_search_config}
    config.update(kwargs)
    Entrez.email = config.pop('email')

    config['term'] = query
    handle = Entrez.esearch(**config)

    results = Entrez.read(handle)
    return results

# Query documents by scraping pubmed webpage
def search_v2(query, **kwargs):

    config = {**default_search_config}
    config.update(kwargs)

    base_url = 'https://pubmed.ncbi.nlm.nih.gov'

    query_params = {
        'term': query,
        'format': 'pmid',
        'size': config['retmax']
    }
    
    res = requests.get(base_url, params=query_params)
    
    soup = Soup(res.text, features='html.parser')
    pmids = soup.find('pre', {'class':'search-results-chunk'}).text

    pmids = re.sub('\s+', ' ', pmids).split(' ')
    
    return {
        'IdList': pmids
    }

def search(query, **kwargs):
    return search_v2(query, **kwargs)

def fetch_details(id_list, **kwargs):

    config = {**default_search_config}
    config.update(kwargs)

    config['ids'] = ','.join(id_list)
    Entrez.email = config.pop('email')

    handle = Entrez.efetch(db = config['db'], retmode=config['retmode'], id=config['ids'])
    papers_details = Entrez.read(handle)
    papers = []
    
    for j, paper in enumerate(papers_details['PubmedArticle']):
        article = paper['MedlineCitation']['Article']
        
        # Retreive Abstract if present
        if 'Abstract' in article:
            abstract_text = ' '.join(article['Abstract']['AbstractText'])
        else:
            abstract_text = ''
        
        # Listed Keywords
        kw_lists = paper['MedlineCitation']['KeywordList']
        kws = sorted(set([str(kw) for kw_list in kw_lists for kw in kw_list]))
        
        papers.append({
            'id': id_list[j],
            'title': article['ArticleTitle'],
            'abstract': abstract_text,
            'keywords': kws[:15]
        })
        
    return pd.DataFrame(papers)


'''
Construct query from tuple & list representation

examples:
[a, b, c] -> a OR b OR c
(a, b, c) -> a AND b AND c
[(a, b), c] -> (a AND b) OR c
'''
def construct_query(dnf):
    
    if isinstance(dnf, str):
        return f'({dnf}[Title/Abstract])'
    
    output = []
    for clause in dnf:
        output.append(construct_query(clause))
    
    if isinstance(dnf, list):
        return '(' + ' AND '.join(output) + ')'
    
    else: # isinstance(tuple, dnf):
        return '(' +  ' OR '.join(output) + ')'


if __name__ == '__main__':
    query = [('PFS'), ('Clinical Trial')]
    query_str = construct_query(query)
    res = search(query_str, retmax=100)
    df = fetch_details(res['IdList'])
    print(df)
