import requests
import pandas as pd
import json
import os


def parse_house():
    url = 'https://www.zillow.com/search/GetSearchPageState.htm'

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    houses = []
    for page in range(1, 3):
        params = {
            "searchQueryState": json.dumps({
                "pagination": {"currentPage": page},
                "usersSearchTerm": "La Jolla, San Diego, CA",
                "mapBounds": {
                    "west": -117.31402417204882,
                    "east": -117.19557782195116,
                    "south": 32.8007253011325,
                    "north": 32.89504192800182
                },
                "mapZoom": 13,
                "regionSelection": [
                    {
                        "regionId": 46087, "regionType": 8
                    }
                ],
                "isMapVisible": False,
                "filterState": {
                    "fore": {"value": False},
                    "mf": {"value": False},
                    "ah": {"value": True},
                    "auc": {"value": False},
                    "nc": {"value": False},
                    "fr": {"value": True},
                    "land": {"value": False},
                    "manu": {"value": False},
                    "fsbo": {"value": False},
                    "cmsn": {"value": False},
                    "fsba": {"value": False}},
                "isListVisible": True
            }),
            "wants": json.dumps(
                {
                    "cat1": ["listResults"]
                }
            ),
            "requestId": 3
        }

        # send request
        page = requests.get(url, headers=headers, params=params)

        # get json data
        json_data = page.json()

        # loop via data
        for house in json_data['cat1']['searchResults']['listResults']:
            houses.append(house)
    return houses


def get_dfs(houses):
    keys = houses[0].keys()
    diff = []
    for i in range(len(houses)):
        if keys != houses[i].keys():
            diff.append(i)
    df = pd.DataFrame(houses)
    df1 = df.loc[~df.index.isin(diff)].dropna(axis=1)
    df2 = df.loc[df.index.isin(diff)].dropna(axis=1)
    return df1, df2


def store():
    houses = parse_house()
    df = pd.DataFrame(houses)
    fname = "zillow.csv"
    if os.path.isfile(fname):
        past = pd.read_csv(fname)
        past['providerListingId'] = past['providerListingId'].astype(str)
        new = past.merge(df, on='providerListingId', how='left')
        print('Total houses added - {}'.format(len(new) - len(past)))
        new.to_csv("zillow.csv", index=False)
    else:
        df.to_csv("zillow.csv", index=False)
        print('Total houses added - {}'.format(len(houses)))


store()
