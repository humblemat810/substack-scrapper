# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 15:51:33 2022

@author: humblemat810
"""

category_chosen = 'business'
category_mapping = {"finance" : 153, 'business' : 62}
category_number = category_mapping[category_chosen]
"""sample query
business : https://substack.com/api/v1/category/public/62/all?page=5
finance : https://substack.com/api/v1/category/public/153/all?page=3
"""
import requests
from sqlitedict import SqliteDict
from scrape_single_channel import get_meta
import pathlib
#%%

cnt_page = 0
total = 0
has_more = True

with SqliteDict(category_chosen + ".sqlite") as mydict:
    while has_more:
        
        uri = "https://substack.com/api/v1/category/public/"+ str(category_number) +"/all?page=" + str(cnt_page)
        print(uri)
        res = requests.get(uri)
        
        total += len(res.json()['publications'])
        has_more = res.json()['more']
        for i in res.json()['publications']:
            mydict[i['id']] = i
        mydict.commit()
        
        cnt_page += 1
        
#%%
with SqliteDict("business_meta.sqlite") as metadict:
    with SqliteDict("business.sqlite") as mydict:
        for k, v in mydict.items():
            if k not in metadict:
                base_url = v['base_url']
                n_article, cnt, i_oldest_article, oldest_response, newest_response = get_meta(base_url)
                new_entry = {
                        "first_post_date" : None,
                        "latest_post_date" : None,
                        "n_article" : n_article,
                        "paid" : (v['draft_plans'] is None)
                    }
                new_entry["first_post_date"] = oldest_response.get('post_date')
                new_entry["latest_post_date"] = newest_response.get('post_date')
                metadict[k] = new_entry
                metadict.commit()
                import time
                time.sleep(5)
import pandas as pd
df_out = pd.DataFrame(['first_post_date', 'latest_post_date', 'n_article', 'paid'])
records = []
with SqliteDict(category_chosen + "_meta.sqlite") as metadict:
    with SqliteDict(category_chosen + ".sqlite") as mydict:
        for k, v in metadict.items():
            d2 = {'id': k}
            d2.update(v)
            records.append(d2)
            
df_out = pd.DataFrame.from_records(records).set_index('id')
df_out.to_csv(category_chosen + '.csv')