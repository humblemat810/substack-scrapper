# Webscraping Substack metadata

## Overview

This article is going to demonstrate a web-scraper of substack metadata and store it using mysqlite database using sqldict API.


There are a few approaches to this problem

1. parse the HTML rendered to see if there is any pattern
2. look for tricks/ API

At this point, we are reverse engienering the existing website and we do not know whether we have luck.

## Initial exploration

The first step to take is to check their website to see anything useful.

Checking the website and say we are now scraping for the financial topics under the link: https://substack.com/discover/category/finance/all

As we see, this website is tricky, it loads more blog description when you click on
"read more" button at the bottom

One of the easiest way to monitor requests is to check the 'network' section of your browser. Press "F12" and go to the network section


What we found open clicking "Read more" is a bunch of requests and we inspect one by one. We found something interesting. The first requests that newly emerged is 'https://substack.com/api/v1/category/public/153/all?page=1'. This requests is special as we see it has the url /api/v1, which is strongly suggesting that this is an API to access the data. How lucky we are!

Here is how we can interpret the API logic. 153 correspond to finance

![](/./img/network.png)

Let's inspect the API results by running some simple code snippets
I am running it on spyder REPL console.

```python
import requests
from sqlitedict import SqliteDict
import pathlib

uri = "https://substack.com/api/v1/category/public/"+ str(category_number) +"/all?page=" + str(cnt_page)
        print(uri)
        res = requests.get(uri)

# my results on my console
In[30]: type(res.json())
Out[30]: dict

In[31]: res.json().keys()
Out[31]: dict_keys(['publications', 'more'])
```

We can see that the results is a dictionary of 2 keys
'more' is a boolean value showing that there is anymore to load.
so we can already have a logic of scraping using "while has_more:"

Let's take a further look at publications

```python
In[34]:type(res.json()['publications'])
Out[34]: list

In[35]:len(res.json()['publications'])
Out[35]: 25
```

Because the susbtack website says that it does not have any open API (https://support.substack.com/hc/en-us/articles/360038433912-Does-Substack-have-an-API- , interesting to see it ending with a hyphen), we need to really make educated guesses.
An educated guest is that publications is a lists of objects with each representing an author. Lets confirm this:

```python
In[37]: res.json()['publications'][-1].keys()
Out[37]: dict_keys(['id', 'name', 'type', 'homepage_type', 'logo_url', 'logo_url_wide', 'cover_photo_url', 'subdomain', 'author_id', 'copyright', 'custom_domain', 'custom_domain_optional', 'email_from', 'trial_end_override', 'email_from_name', 'support_email', 'hero_image', 'hero_text', 'hide_intro_title', 'hide_intro_subtitle', 'require_clickthrough', 'theme_var_background_pop', 'default_coupon', 'community_enabled', 'theme_var_cover_bg_color', 'flagged_as_spam', 'theme_var_color_links', 'default_group_coupon', 'email_banner_url', 'created_at', 'podcast_enabled', 'page_enabled', 'apple_pay_disabled', 'fb_pixel_id', 'ga_pixel_id', 'twitter_pixel_id', 'parsely_pixel_id', 'keywee_pixel_id', 'podcast_title', 'podcast_art_url', 'podcast_description', 'podcast_feed_url', 'image_thumbnails_always_enabled', 'hide_podcast_feed_link', 'embed_tracking_disabled', 'minimum_group_size', 'parent_publication_id', 'bylines_enabled', 'byline_images_enabled', 'post_preview_limit', 'google_site_verification_token', 'fb_site_verification_token', 'google_tag_manager_token', 'language', 'paid_subscription_benefits', 'free_subscription_benefits', 'founding_subscription_benefits', 'parent_about_page_enabled', 'invite_only', 'subscriber_invites', 'default_comment_sort', 'rss_website_url', 'rss_feed_url', 'sibling_rank', 'payments_state', 'default_show_guest_bios', 'chartable_token', 'expose_paywall_content_to_search_engines', 'podcast_byline', 'paywall_free_trial_enabled', 'show_pub_podcast_tab', 'theme', 'plans', 'stripe_user_id', 'stripe_country', 'stripe_publishable_key', 'author_name', 'author_photo_url', 'author_bio', 'has_child_publications', 'public_user_count', 'has_posts', 'first_post_date', 'has_podcast', 'has_subscriber_only_podcast', 'has_community_content', 'twitter_screen_name', 'rankingDetail', 'rankingDetailFreeIncluded', 'contributors', 'tier', 'no_follow', 'no_index', 'can_set_google_site_verification', 'can_have_sitemap', 'draft_plans', 'base_url', 'hostname', 'is_on_substack', 'parent_publication', 'child_publications', 'sibling_publications', 'multiple_pins'])

```

We can see a large dict object containing all neccessary information.

## Crawling metadata of all weblogs

We are going to store it in a sqlite database with a dict api. 

sqlitedict is a library that uses sqlite to make a persistent dict that can be accessed like ordinary dict object.

We are using context manger to write more error prone code.

```python

category_chosen = 'finance'
cnt_page = 0
total = 0
has_more = True
category_number = 153
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
```

## Crawling meta of each weblog page

Now we have collected the weblog metadata.
As our goal now is to scrape article metadata on each of the weblog, we just need to get the url of each and neglect others and scrape from each blog's website.

We can confirm the structure by visiting one of the weblog for example here
https://categorypirates.substack.com

We can get all the archive under the 'archive' section.
Again this is not a static website with all data loaded.
The archive page is an infinite scrolling page. As we scroll down to the bottom, older articles are loaded from the page. If we are writing a robot to do the meta collection task, we need to read the data dynamically as new data is loaded if we do it manually and it is extremely tedious. 
However, we are using the same F12 API trick as previously did, as shown in the figure below.

![](/./img/category_pirate.png)

We can copy the api link by right-clicking the request URL on a chrome browser.

We found the API link to be

```python
base_url + '/api/v1/archive?sort=new&search=&offset=' + str(offset) + '&limit=' + str(limit)

#example: https://categorypirates.substack.com/api/v1/archive?sort=new&search=&offset=12&limit=12
```

Here I am explaining the API of the snippet code above. "Offset" means how many articles from the newest. For example offset = 1 means the second-newest article. "Limit" is the batch size, representing how many articles to return in one request.

Our task is to crawl how many article and the date of the oldest article from an infinite scrolling page.

### Task statement

The task is, finding the length of an array by asking the existence of a range. The response can be:

1. all exist -> a full list with length same as limit
2. only exist up to index i, partial list with length equals to i
3. all non-exist -> indicated by a returned empty list

So the API only return a list of length l between 0 to l 

### Technical consideration: Stealth or not? Linear or optimised

If we are ensuring complete stealth, we need to use a robot, or at least,
Make request linearly
    The pros are:
        
- Stay undetected, no one will stop me from doing the same everyday to update the statistics
- Linear crawling is easy to implement.

And the cons are:

- The crawling may impose high loading on the API server and create funny statistics to their internal data analyst/ maintenence.
- Crawling lots of unuseful information and waste resource on the client side

My decision is, I am trying to be nice not to kill their server while stay easily detected.


My searching algorithm is as follows (full implentation will be shown in the later part of the article):

1. Set head = 0, mid = head + limit, tail = head + 2 * limit, this is for initial search.
send query to check the ranges starting from head, mid and tail. Here we use the query function to query an url with range.
```python
head_request_result = query(base_url, offset = head)
mid_request_result = query(base_url, offset = mid)
tail_request_result = query(base_url, offset = tail)
```

2. If any of the search returns an incomplete list, the tail of the array is within the range.
For example, if I request the range from 24 to 36 and only 7 records is returned,
the number of total articles is  24 + 7 = 31.



3. If the tail returns full list, it means that the true length is longer and need to search a longer range. We will update the list by setting the follow updates.
```python
head, mid, tail = mid, tail, tail * 2
head_request_result, mid_request_result, tail_request_result = mid_request_result, tail_request_result, query(base_url, tail)
```


4. if mid return empty list, the array length is between head and mid, we can update the search as
```python
tail = mid
mid = (head + tail) / 2

mid_request_result, tail_request_result = query(base_url, mid), mid_request_result

```


5. if mid return full list and tail return empty list, the end of array lies between mid and tail and update search as below
```python
head = mid
mid = (head + tail) / 2

mid_request_result, head_request_result = query(base_url, mid), mid_request_result
```

The full implementation of the metadata scraping is posted on https://github.com/humblemat810/substack-scrapper/blob/main/scrape_single_channel.py

When the logic of scraping a single weblog is worked out, we use the previously scraped list of all weblogs to start scraping the metadata of each weblog. Note that in order not to overload the target API server, a sleep of 5 seconds was intentionally added to average out the server workload

```python
with SqliteDict(category_chosen + "_meta.sqlite") as metadict:
    with SqliteDict(category_chosen + ".sqlite") as mydict:
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
```


Here we are storing the metadata in a different sqlite file in form of {topic}_meta.sqlite while the actual data of each weblog site is stored in {topic}.sqlite. For example, the finance metadata will be stored as finance_meta.sqlite while its details is in "finance.sqlite".



```python
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

```

At the end, we would like to export the data to csv using pandas. We use pandas.DataFrame.from_records to convert a list of dict into a pandas dataframe, and then export to csv file.

Let's produce some simple summary statistics using the dataset
Lets see the difference between paid and free subscription articles and their frequencies. We are calculating the average number of days between subsequent release of articles.

```python

from datetime import datetime

datetime_object = datetime.strptime(df_out['first_post_date'][0], '%Y-%m-%dT%H:%M:%S.%fZ')

df_out['first_post_date'] = pd.to_datetime(df_out['first_post_date'])
df_out['latest_post_date'] = pd.to_datetime(df_out['latest_post_date'])
df_out['article_production_days'] = ((df_out['latest_post_date'] - df_out['first_post_date']) / df_out['n_article'] ).dt.days

df_summary = df_out.drop('n_article', axis = 1).groupby(by='paid').mean()

from matplotlib import pyplot as plt
plt.figure(figsize = [6, 9])
plt.axes()
h_plot = plt.bar(range(len(df_summary.index)), df_summary['article_production_days'], width = 0.5)
plt.xticks([0,1], labels = ['free','paid'])
plt.xlabel('subscription mode')
plt.ylabel('days to produce an article')


             article_production_days
paid
False                 5.015038
True                 19.415254
```

![](/./img/proportion_of_subscription_weblogger_free_vs_paid.png)

We see substantial difference between the number of days. Free subscriptions produces an article every 5 days while paid ones takes 19.4 days on average to release an article. One of the possible reason is that, the paid ones are more polish for commercial grade while the free ones are shallower (comparatively insights).

```python
df_pie = df_out.drop(['first_post_date', 'latest_post_date', 'article_production_days', 'n_article'], axis = 1)
df_num_of_paid_summary = df_pie.reset_index().set_index('paid').groupby('paid').count()
df_n_paid_article = df_out.drop(['first_post_date', 'latest_post_date', 'article_production_days'], axis = 1)
df_n_paid_article.where(df_n_paid_article['paid'], 0).sum()
df_n_paid_article.where(~df_n_paid_article['paid'],0).sum()
plt.figure(figsize = (6,5) )
plt.pie(df_num_of_paid_summary['id'])
plt.legend([ 'free', 'paid'])
```
![](/./img/proportion_of_article_free_vs_paid.png)

We can see that the number of paid subscription authors is similar to that of their free counterparts.