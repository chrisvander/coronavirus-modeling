import json
import requests
from urllib.parse import urlencode

headers = {
    "Content-Type": "application/json"
}


def parse_query(query):
    """ Convert all lists to strings within a given query dict. """

    ret = {}
    for k, v in query.items():
        if isinstance(v, list):
            ret[k] = ",".join(v)
        else:
            ret[k] = v
    return ret


def get_json(url, query=None):
    """ Perform a GET request and return the resulting JSON payload as an object. """

    res = requests.get(url, params=query, headers=headers)
    if res.status_code == 200:
        return json.loads(res.content.decode("utf-8"))
    else:
        print("Response code:", res.status_code)
        print(res.content)
        return None
