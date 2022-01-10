import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import re
import time
import random
import csv
import cronitor
from datetime import date

# cronitor.api_key = 'db021f17534f4c29be499dd11edbb6ba'
#
# cronitor.Monitor.put(
#     key='Scrape Craigslist',
#     type='job',
#     schedule='@daily',
#     notify='slack:devops-alerts'
# )

fieldnames = [
    'url',
    'post_id',
    'post_date',
    'description',
    'num_beds',
    'num_baths',
    'price',
    'address',
    'sqft',
    'features'
]

# @cronitor.job('Scrape Craigslist')

def scrape_housing_links(dist = 10, postal = 92037,
    url = "https://sandiego.craigslist.org/d/apartments-housing-for-rent/search/apa?s={page}&availabilityMode=0&postal={zip_code}&search_distance={miles}"
    ):
    """
    Function that takes in two parameters, distance in miles and the zip code we are performing our search in.
    It will search postings within the set radius around the zip code and save its links
    dist: int
    postal: int
    url: string of the website of the craigslist site, default is the san diego craigslist.
    returns: a set of links to scrape
    """
    # Find the county we are searching in
    county = re.match("^https:\/\/([\w]+).craigslist.org", url).group(1)
    posting_links = set()
    # Find all of the links that redirects to the posting on craigslist
    temp_url = url.format(miles = dist, zip_code = postal, page = 0)
    listing = requests.get(temp_url)
    content = listing.text
    soup = BeautifulSoup(content, 'html.parser')
    # find the number of search results
    total_count = int(soup.find('span', attrs = {'class': 'totalcount'}).text)
    # We land on the first page and every page lists 120 postings
    current, num_results_on_a_page = 0, 120
    while current < total_count:
        # Access the website and parse the webpage
        time.sleep(random.randint(2, 10))
        temp_url = url.format(miles = dist, zip_code = postal, page = current)
        listing = requests.get(temp_url)
        content = listing.text
        soup = BeautifulSoup(content, 'html.parser')
        htmls = soup.find_all('a', attrs = {'class': 'result-title hdrlnk'})
        for link in htmls:
            # Filter out the sponsored results
            address = link.get('href')
            if county in address:
                posting_links.add(address)
        current += num_results_on_a_page
    return posting_links

def scrape_basic_info(post):
    """
    Input: post takes in a soup object of a craigslist posting
    and returns the post_id and post_date in a tuple
    """
    url = post.find("meta", property="og:url").get('content')
    if url is None:
        post_id = None
    else:
        post_id = re.search('([\d]+).html', url).group(1)
    post_date = post.find('time', attrs = {'class': 'date timeago'}).get('datetime')
    return {
        'url': url,
        'post_id': post_id,
        'post_date': post_date
    }

def scrape_listing_info(post):
    """
    Input: post takes in a soup object of a craigslist posting
    Returns: a number of bedrooms, bathrooms, price, address,
    and the size of the listing as a dictionary
    """
    price = post.find('span', attrs = {'class': 'price'})
    if price is not None:
        price = price.text.strip('$').replace(',', '')
    else:
        price = -1
    temp = post.find('span', attrs = {'class': 'shared-line-bubble'}).text.split('/')
    if temp is None:
        num_beds = -1
        num_baths = -1
    else:
        temp = [i.strip() for i in temp]
        if len(temp) == 2: # listed both the number of bathrooms and bedrooms
            num_beds = int(temp[0].lower().strip('br'))
            num_baths = temp[1].lower().strip('ba')
        elif len(temp) == 1: # Listed one but not the other
            if "br" in temp[0].lower():
                num_beds = temp[0].lower().strip('br')
                num_baths = -1
            elif "ba" in temp[0].lower():
                num_beds = -1
                num_baths = temp[0].lower.strip("ba")
    #unable to scrape address if there is none
    address = post.find('div', attrs = {'class': 'mapaddress'})
    if address is not None:
        address = address.text
    sqft = post.find_all('span', attrs = {'class': 'shared-line-bubble'})
    if len(sqft) == 2 and 'ft2' in sqft[1].text:
        sqft = sqft[1].text.strip('ft2')
    else:
        sqft = -1
    return {
        'num_beds': num_beds,
        'num_baths': num_baths,
        'price': price,
        'address': address,
        'sqft': sqft
    }

def scrape_desc(post):
    """
    Input: post takes in a soup object of a craigslist posting
    Returns: a dictionary of the string of the description
    for the posting by the poster
    """
    description = post.find('section', attrs = {'id': 'postingbody'})
    if description is not None:
        description = description.text.strip().strip('QR Code Link to This Post\n\n\n')
    return {'description': description}

def scrape_features(post, feature_vector = {}):
    """
    Input: post takes in a soup object of a craigslist posting
    feature vector is a dictionary of keys with value 0
    Returns a number of features indicated by the poster
    """
    # might be modifying every feature vector instead
    search = post.find_all('p', attrs = {'class': 'attrgroup'})

    if len(search) == 2: # posting has listed attributes
        # app_fee_found = False
        attributes = [i.text for i in search[1].find_all('span')]
        feature_vector['features'] = attributes
        # for attr in attributes:
            # if "application fee" in attr:
                # app_fee_found = True
                # fee = re.search("\$([\d]+)", attr)
                # if fee is not None:
                    # feature_vector['application fee'] = fee.group(1)
                # else:
                    # feature_vector['application fee'] = -1
            # else:
                # feature_vector[attr] = 1
        # if app_fee_found == False:
            # feature_vector['application fee'] = -1
    else:
        feature_vector['features'] = []
    return feature_vector

def scrape_post(post):
    # if the post is removed
    if post.find('div', attrs = {'class': 'removed'}) is not None:
        return None
    row = dict()
    post_info = scrape_basic_info(post)
    row.update(post_info)
    description = scrape_desc(post)
    row.update(description)
    info = scrape_listing_info(post)
    row.update(info)
    features = scrape_features(post)
    row.update(features)
    return row

def write_to_csv(post):
    """
    Writes to the csv file
    """
    with open('craigslist.csv', mode='a+') as df:
        writer = csv.DictWriter(df, fieldnames = fieldnames, extrasaction='ignore', restval = None)
        parsed_data = scrape_post(post)
        if parsed_data is not None:
            writer.writerow(parsed_data)

def scrape_webpages(links):
    """
    links is an iterable
    returns a list of soup objects
    """
    for link in links:
        time.sleep(random.randint(2, 10))
        listing = requests.get(link)
        content = listing.text
        soup = BeautifulSoup(content, features = 'lxml')
        if soup is None:
            continue
        write_to_csv(soup)

def scrape_pages():
    """
    Pipeline to streamline scraping for websites and download the webpage
    """
    # Download links of relevent postings
    links = scrape_housing_links()

    # Add new postings to the list of scrapped postings
    with open('scrapped.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip the headers
        scrapped_links = set([link[0] for link in reader])

    with open('scrapped.csv', mode='a') as f:
        # remove duplicate links that has been downloaded before
        # Still need to remove duplicates with the same post id
        # but different url (due to change in title of the post)
        writer = csv.DictWriter(f, fieldnames = ["link"])
        to_download = links.difference(scrapped_links)
        for link in to_download:
            temp = {"link": link}
            writer.writerow(temp)

    # Scrape the webpage and save it to a csv file
    scrape_webpages(to_download)

def rescrape():
    """
    Scrapped the pages that were left off due to an interruption of
    the scrape_pages function that left a discrepency between the
    number of scrapped pages and actual entries in craigslist.csv
    """
    with open('scrapped.csv', mode='r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip the headers
        links = set([link[0] for link in reader])
    df = pd.read_csv('craigslist.csv')
    scrapped_listings = set(df.loc[:, 'url'].tolist())
    to_download = links.difference(scrapped_listings)
    scrape_webpages(to_download)

def scraper():
    try:
        print('Initiating Scraping Process')
        scrape_pages()
    except:
        print('Scraping terminated or interrupted. Restarting Operation')
        rescrape()
    finally:
        print('Ensuring that all web pages are scraped.')
        rescrape()
        print('Done')

scraper()
with open('scrape_log.txt', mode = 'a') as f:
    f.write('Scrape completed on {}'.format(date.today()))
